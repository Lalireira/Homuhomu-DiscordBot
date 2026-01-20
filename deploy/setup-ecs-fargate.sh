#!/bin/bash
# AWS ECS (Fargate) 初期セットアップスクリプト

set -e

# 設定変数
AWS_REGION="ap-northeast-1"
ECR_REPOSITORY="homuhomu-discordbot"
CLUSTER_NAME="homuhomu-bot-cluster"
SERVICE_NAME="homuhomu-bot-service"
TASK_FAMILY="homuhomu-bot-task"
EXECUTION_ROLE_NAME="ecsTaskExecutionRole"
LOG_GROUP_NAME="/ecs/homuhomu-bot"

echo "=========================================="
echo "Homuhomu Discord Bot - ECS Fargate Setup"
echo "=========================================="
echo ""
echo "このスクリプトは以下を自動的にセットアップします:"
echo "1. ECRリポジトリの作成"
echo "2. ECSクラスターの作成"
echo "3. CloudWatch Logsグループの作成"
echo "4. IAMロールの作成（ecsTaskExecutionRole）"
echo "5. VPC情報の取得"
echo ""
read -p "続行しますか？ (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "キャンセルしました。"
    exit 0
fi

# AWSアカウントIDを取得
echo ""
echo "[*] AWSアカウントIDを取得中..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWSアカウントID: $AWS_ACCOUNT_ID"

# Step 1: ECRリポジトリの作成
echo ""
echo "[1/6] ECRリポジトリを作成中..."
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION > /dev/null 2>&1; then
    echo "⚠️  ECRリポジトリは既に存在します: $ECR_REPOSITORY"
else
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY \
        --region $AWS_REGION > /dev/null
    echo "✅ ECRリポジトリを作成しました: $ECR_REPOSITORY"
fi
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
echo "   URI: $ECR_URI"

# Step 2: ECSクラスターの作成
echo ""
echo "[2/6] ECSクラスターを作成中..."
if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    echo "⚠️  ECSクラスターは既に存在します: $CLUSTER_NAME"
else
    aws ecs create-cluster \
        --cluster-name $CLUSTER_NAME \
        --region $AWS_REGION > /dev/null
    echo "✅ ECSクラスターを作成しました: $CLUSTER_NAME"
fi

# Step 3: CloudWatch Logsグループの作成
echo ""
echo "[3/6] CloudWatch Logsグループを作成中..."
if aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP_NAME --region $AWS_REGION --query "logGroups[?logGroupName=='$LOG_GROUP_NAME']" --output text | grep -q "$LOG_GROUP_NAME"; then
    echo "⚠️  CloudWatch Logsグループは既に存在します: $LOG_GROUP_NAME"
else
    aws logs create-log-group \
        --log-group-name $LOG_GROUP_NAME \
        --region $AWS_REGION
    echo "✅ CloudWatch Logsグループを作成しました: $LOG_GROUP_NAME"
fi

# Step 4: IAMロールの作成
echo ""
echo "[4/6] IAMロール（ecsTaskExecutionRole）を作成中..."

# ロールが既に存在するか確認
if aws iam get-role --role-name $EXECUTION_ROLE_NAME > /dev/null 2>&1; then
    echo "⚠️  IAMロールは既に存在します: $EXECUTION_ROLE_NAME"
    EXECUTION_ROLE_ARN=$(aws iam get-role --role-name $EXECUTION_ROLE_NAME --query 'Role.Arn' --output text)
else
    # 信頼ポリシーファイルを作成
    cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # ロールを作成
    aws iam create-role \
        --role-name $EXECUTION_ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json > /dev/null
    
    # AWSマネージドポリシーをアタッチ
    aws iam attach-role-policy \
        --role-name $EXECUTION_ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    # Secrets Managerへのアクセス権限を追加
    cat > /tmp/secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:homuhomu-bot/*"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name $EXECUTION_ROLE_NAME \
        --policy-name SecretsManagerAccess \
        --policy-document file:///tmp/secrets-policy.json
    
    echo "✅ IAMロールを作成しました: $EXECUTION_ROLE_NAME"
    
    # ロールのARNを取得
    sleep 5  # ロールが反映されるまで待機
    EXECUTION_ROLE_ARN=$(aws iam get-role --role-name $EXECUTION_ROLE_NAME --query 'Role.Arn' --output text)
    
    # 一時ファイルを削除
    rm /tmp/trust-policy.json /tmp/secrets-policy.json
fi

echo "   ARN: $EXECUTION_ROLE_ARN"

# Step 5: VPC情報の取得
echo ""
echo "[5/6] VPC情報を取得中..."

# デフォルトVPCを取得
DEFAULT_VPC=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text \
    --region $AWS_REGION)

if [ "$DEFAULT_VPC" == "None" ] || [ -z "$DEFAULT_VPC" ]; then
    echo "⚠️  デフォルトVPCが見つかりません。手動でVPCとサブネットを指定してください。"
    DEFAULT_VPC="vpc-xxxxx"
    SUBNETS="subnet-xxxxx"
    SECURITY_GROUP="sg-xxxxx"
else
    echo "✅ デフォルトVPC: $DEFAULT_VPC"
    
    # パブリックサブネットを取得（最初の2つ）
    SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$DEFAULT_VPC" "Name=default-for-az,Values=true" \
        --query 'Subnets[0:2].SubnetId' \
        --output text \
        --region $AWS_REGION | tr '\t' ',')
    
    echo "✅ サブネット: $SUBNETS"
    
    # セキュリティグループを作成または取得
    SG_EXISTS=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=homuhomu-bot-sg" "Name=vpc-id,Values=$DEFAULT_VPC" \
        --query 'SecurityGroups[0].GroupId' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "None")
    
    if [ "$SG_EXISTS" == "None" ] || [ -z "$SG_EXISTS" ]; then
        SECURITY_GROUP=$(aws ec2 create-security-group \
            --group-name homuhomu-bot-sg \
            --description "Security group for Homuhomu Discord Bot (ECS Fargate)" \
            --vpc-id $DEFAULT_VPC \
            --query 'GroupId' \
            --output text \
            --region $AWS_REGION)
        echo "✅ セキュリティグループを作成しました: $SECURITY_GROUP"
    else
        SECURITY_GROUP=$SG_EXISTS
        echo "✅ 既存のセキュリティグループを使用: $SECURITY_GROUP"
    fi
fi

# Step 6: タスク定義ファイルの更新
echo ""
echo "[6/6] タスク定義ファイルを更新中..."

if [ -f "deploy/ecs-task-definition.json" ]; then
    # タスク定義ファイルのプレースホルダーを実際の値に置き換え
    sed -i.bak \
        -e "s|123456789012|$AWS_ACCOUNT_ID|g" \
        -e "s|arn:aws:iam::[^:]*:role/ecsTaskExecutionRole|$EXECUTION_ROLE_ARN|g" \
        deploy/ecs-task-definition.json
    
    echo "✅ タスク定義ファイルを更新しました"
    rm deploy/ecs-task-definition.json.bak 2>/dev/null || true
else
    echo "⚠️  deploy/ecs-task-definition.json が見つかりません"
fi

# 完了メッセージ
echo ""
echo "=========================================="
echo "✅ セットアップ完了！"
echo "=========================================="
echo ""
echo "📝 次のステップ:"
echo ""
echo "1. AWS Secrets Managerにシークレットを作成:"
echo "   aws secretsmanager create-secret --name homuhomu-bot/discord-token --secret-string \"YOUR_TOKEN\" --region $AWS_REGION"
echo "   aws secretsmanager create-secret --name homuhomu-bot/osu-client-id --secret-string \"YOUR_ID\" --region $AWS_REGION"
echo "   aws secretsmanager create-secret --name homuhomu-bot/osu-client-secret --secret-string \"YOUR_SECRET\" --region $AWS_REGION"
echo "   # 他の環境変数も同様に..."
echo ""
echo "2. タスク定義を登録:"
echo "   aws ecs register-task-definition --cli-input-json file://deploy/ecs-task-definition.json --region $AWS_REGION"
echo ""
echo "3. イメージをビルドしてECRにプッシュ:"
echo "   ./deploy/deploy-to-ecs.sh"
echo ""
echo "4. ECSサービスを作成:"
echo "   aws ecs create-service \\"
echo "       --cluster $CLUSTER_NAME \\"
echo "       --service-name $SERVICE_NAME \\"
echo "       --task-definition $TASK_FAMILY \\"
echo "       --desired-count 1 \\"
echo "       --launch-type FARGATE \\"
echo "       --network-configuration \"awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}\" \\"
echo "       --region $AWS_REGION"
echo ""
echo "📊 作成されたリソース:"
echo "   - ECRリポジトリ: $ECR_URI"
echo "   - ECSクラスター: $CLUSTER_NAME"
echo "   - CloudWatch Logs: $LOG_GROUP_NAME"
echo "   - IAMロール: $EXECUTION_ROLE_ARN"
echo "   - VPC: $DEFAULT_VPC"
echo "   - サブネット: $SUBNETS"
echo "   - セキュリティグループ: $SECURITY_GROUP"
echo ""
echo "=========================================="


