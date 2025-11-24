// data.model.chat.ChatResponse
package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

// 1. [응답] 세션 초기화 결과
data class InitSessionResponse(
    @SerializedName("thread_id") val threadId: String,
    @SerializedName("session_type") val sessionType: String, // "WEEKLY" or "GENERAL"
    @SerializedName("display_message") val displayMessage: String = "",
    @SerializedName("current_week") val currentWeek: Int = 1
)

// 2. [응답] 채팅 응답 결과
data class ChatResponse(
    @SerializedName("reply") val reply: String,
    @SerializedName("is_ended") val isEnded: Boolean,
    @SerializedName("current_week") val currentWeek: Int,
    @SerializedName("week_title") val weekTitle: String,
    @SerializedName("week_goals") val weekGoals: List<String>
)

// 3. 서랍 목록용 데이터 모델
data class SessionSummary(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("title") val title: String,
    @SerializedName("date") val date: String
)