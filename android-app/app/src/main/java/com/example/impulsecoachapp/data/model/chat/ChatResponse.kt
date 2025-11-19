package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

/**
 * /chat/next API로부터 받을 응답(Response) 모델
 *
 * @param sessionId 현재 세션 ID
 * @param reply 어시스턴트의 응답 (채팅 로그 기반)
 * @param state 현재 세션 상태
 * @param isEnded 세션이 종료되었는지 여부
 * @param homework 숙제 (선택 사항)
 */
data class ChatResponse(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("reply") val reply: Reply,
    @SerializedName("state") val state: Map<String, String>, // 또는 더 구체적인 State 클래스
    @SerializedName("is_ended") val isEnded: Boolean,
    @SerializedName("homework") val homework: Map<String, Any>? = null // 또는 Homework 클래스
)

/**
 * 'reply' 객체 모델 (채팅 로그의 주석 기반: { emotion, spending, action })
 */
data class Reply(
    @SerializedName("emotion") val emotion: String,
    @SerializedName("spending") val spending: String,
    @SerializedName("action") val action: String // <-- 이 필드가 실제 말풍선에 표시될 텍스트일 가능성이 높습니다.
)
