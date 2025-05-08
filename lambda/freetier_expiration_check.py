import os
import boto3
from datetime import datetime

def handler(event, context):
    """
    AWS 프리티어 종료 알림을 위한 Lambda 핸들러 함수
    
    계정 생성일로부터 1년 후 종료 시점에 30일, 7일, 1일 전에 SNS 알림을 발송합니다.
    
    Parameters:
        event: Lambda 이벤트 객체
        context: Lambda 컨텍스트 객체
        
    Returns:
        dict: 처리 결과를 포함하는 응답 객체
    """
    account_creation_date = datetime.strptime(os.environ['ACCOUNT_CREATION_DATE'], '%Y-%m-%d')
    today = datetime.now()
    
    # 프리티어 종료일 계산 (계정 생성일로부터 1년)
    freetier_end_date = datetime(account_creation_date.year + 1, account_creation_date.month, account_creation_date.day)
    
    # 남은 일수 계산
    days_remaining = (freetier_end_date - today).days
    
    # 알림 조건: 30일, 7일, 1일 전
    if days_remaining in [30, 7, 1]:
        sns = boto3.client('sns')
        message = f'''
AWS 프리티어 종료 알림

계정 생성일: {account_creation_date.strftime('%Y-%m-%d')}
프리티어 종료일: {freetier_end_date.strftime('%Y-%m-%d')}
남은 일수: {days_remaining}일

프리티어 기간이 종료되면 사용 중인 AWS 서비스에 대해 일반 요금이 부과됩니다.
필요하지 않은 리소스는 삭제하거나 중지하는 것을 권장합니다.
'''
        
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject=f'[중요] AWS 프리티어 종료 {days_remaining}일 전 알림'
        )
        
        return {
            'statusCode': 200,
            'body': f'프리티어 종료 {days_remaining}일 전 알림이 전송되었습니다.'
        }
    
    return {
        'statusCode': 200,
        'body': '알림 조건에 해당하지 않습니다.'
    }
