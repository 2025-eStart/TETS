// 앱 내부 데이터 모델. 레포트 화면, 채팅 화면에 결제내역을 띄울 때 쓰는 transaction 데이터의 형식을 정의한다.
// API에서 받아오는 데이터의 형식(API 모델)과 같을 수도 있지만, 기본적으로 별개이다.

package com.example.impulsecoachapp.data

data class Transaction(
    val transactionId: String,        // 결제 내역 ID = 도큐먼트 ID
    val date: String,                 // 결제 날짜
    val time: String,                 // 결제 시각
    val content: String,              // 결제 내용 (예: "배달음식")
    val amount: Int,                  // 결제 금액
    val method: String,               // 결제 수단 (예: "카드")
    var isImpulsive: Boolean = false, // 충동소비 여부 (초기값: false), 화면에서 사용자가 바꿀 수 있음, 상담에서 바꿀 수 있음

    // 상담 관련 데이터
    // Todo: 챗봇 API 연결 후 summary 수정하기
    val summary: String? = "소비 내용: 배달음식\n원인: 스트레스\n실천할 대체 행동: 10분 산책하기" // 상담 요약 정보 (API를 통해 받아올 데이터)
)