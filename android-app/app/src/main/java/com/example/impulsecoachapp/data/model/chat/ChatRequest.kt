//data.model.chat.ChatRequest

package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

// 1. [요청] 세션 초기화 (/session/init)
data class InitSessionRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("force_new") val forceNew: Boolean = false
)

// 2. [요청] 채팅 메시지 전송 (/chat)
data class ChatRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("thread_id") val threadId: String,
    @SerializedName("message") val message: String,
    @SerializedName("session_type") val sessionType: String
)

// 3. 프로그램 종료 후 리셋 (/session/reset)
data class ResetRequest(
    @SerializedName("user_id") val userId: String
)