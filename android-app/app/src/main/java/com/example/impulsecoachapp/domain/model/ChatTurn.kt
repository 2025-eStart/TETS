// domain.model.ChatTurn
package com.example.impulsecoachapp.domain.model

/**
 * 한 번의 대화 턴(Turn)에서 발생하는 모든 데이터를 포함하는 모델
 *
 * @param assistantMessage 봇의 응답 메시지
 * @param isSessionEnded 상담 종료 여부 (True면 축하/요약 화면 전환)
 * @param currentWeek 현재 진행 중인 주차 (예: 1, 2, ...)
 * @param weekTitle 주차별 상담 제목 (예: "문제 고리 이해")
 * @param weekGoals 이번 주 달성해야 할 목표 리스트 (체크리스트용)
 * @param homework 상담 후 제시된 숙제 ( 일일 리마인더용)
 */

// ChatResponse와 동일한 구조의 Domain 모델 (필요 시 매퍼로 변환하지만, 여기선 편의상 구조 동일하게 사용)
data class Homework(
    val description: String,
    val examples: List<String>
)

data class ChatTurn(
    val assistantMessage: ChatMessage,
    val isSessionEnded: Boolean,
    val currentWeek: Int = 1,
    val weekTitle: String? = null,
    val weekGoals: List<String> = emptyList(),
    val homework: Homework? = null
)
