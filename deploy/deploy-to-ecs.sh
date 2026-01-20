#!/bin/bash
# AWS ECS (Fargate) デプロイスクリプト

set -e

# 設定変数
AWS_REGION="ap-northeast-1"
AWS_ACCOUNT_ID=""
ECR_REPOSITORY="homuhomu-discordbot"
CLUSTER_NAME="homuhomu-bot-cluster"
SERVICE_NAME="homuhomu-bot-service"
TASK_FAMILY="homuhomu-bot-task"

echo "=========================================="
echo "Homuhomu Discord Bot - ECS Fargate Deploy"
echo "=========================================="

# AWSアカウントIDを取得
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "[*] AWSアカウントIDを取得中..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "✅ AWSアカウントID: $AWS_ACCOUNT_ID"
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

# Step 1: ECRにログイン
echo ""
echo "[1/5] ECRにログイン中..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
echo "✅ ECRログイン成功"

# Step 2: Dockerイメージをビルド
echo ""
echo "[2/5] Dockerイメージをビルド中..."
docker build -t $ECR_REPOSITORY:latest .
echo "✅ ビルド完了"

# Step 3: イメージにタグ付け
echo ""
echo "[3/5] イメージにタグ付け中..."
docker tag $ECR_REPOSITORY:latest $ECR_URI:latest
docker tag $ECR_REPOSITORY:latest $ECR_URI:$(date +%Y%m%d-%H%M%S)
echo "✅ タグ付け完了"

# Step 4: ECRにプッシュ
echo ""
echo "[4/5] ECRにプッシュ中..."
docker push $ECR_URI:latest
docker push $ECR_URI:$(date +%Y%m%d-%H%M%S)
echo "✅ プッシュ完了"

# Step 5: ECSサービスを更新（既存の場合）
echo ""
echo "[5/5] ECSサービスを更新中..."

# サービスが存在するか確認
SERVICE_EXISTS=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].status' \
    --output text 2>/dev/null || echo "MISSING")

if [ "$SERVICE_EXISTS" != "MISSING" ] && [ "$SERVICE_EXISTS" != "None" ]; then
    echo "[*] 既存のサービスを更新します..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --force-new-deployment \
        --region $AWS_REGION > /dev/null
    echo "✅ サービス更新完了"
else
    echo "[!] サービスが存在しません。手動でサービスを作成してください。"
    echo ""
    echo "以下のコマンドを実行してサービスを作成:"
    echo ""
    echo "aws ecs create-service \\"
    echo "    --cluster $CLUSTER_NAME \\"
    echo "    --service-name $SERVICE_NAME \\"
    echo "    --task-definition $TASK_FAMILY \\"
    echo "    --desired-count 1 \\"
    echo "    --launch-type FARGATE \\"
    echo "    --network-configuration \"awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}\" \\"
    echo "    --region $AWS_REGION"
fi

echo ""
echo "=========================================="
echo "✅ デプロイ完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. サービスの状態を確認:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"
echo ""
echo "2. ログを確認:"
echo "   aws logs tail /ecs/homuhomu-bot --follow --region $AWS_REGION"
echo ""
echo "3. タスクの一覧を表示:"
echo "   aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --region $AWS_REGION"
echo ""
echo "=========================================="


