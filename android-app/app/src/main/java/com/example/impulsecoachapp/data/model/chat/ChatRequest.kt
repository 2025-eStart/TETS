//data.model.chat.ChatRequest
package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

/**
 * /chat/next API로 보낼 요청(Request) 모델
 *
 * @param uid Firebase UID
 * @param text 사용자가 입력한 메시지
 * @param week 주차 (선택 사항)
 * @param stepHint (선택 사항)
 * @param end 이 메시지로 세션을 종료할지 여부 (기본 false)
 */
data class ChatRequest(
    @SerializedName("uid") val uid: String,
    @SerializedName("text") val text: String,
    @SerializedName("week") val week: Int? = null,
    @SerializedName("step_hint") val stepHint: String? = null,
    @SerializedName("end") val end: Boolean = false
)
