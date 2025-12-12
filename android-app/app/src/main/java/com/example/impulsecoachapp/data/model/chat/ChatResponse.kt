// data.model.chat.ChatResponse
package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

// 1. [응답] 세션 초기화 결과
data class InitSessionResponse(
    @SerializedName("thread_id") val threadId: String,
    @SerializedName("session_type") val sessionType: String, // "WEEKLY" or "GENERAL"
    @SerializedName("display_message") val displayMessage: String = "",
    @SerializedName("current_week") val currentWeek: Int = 1,
    @SerializedName("is_weekly_in_progress") val isWeeklyInProgress: Boolean  = false,
    @SerializedName("status") val status: String? = "active"
)

// 2. [응답] 채팅 응답 결과
data class ChatResponse(
    @SerializedName("reply") val reply: String,
    @SerializedName("is_ended") val isEnded: Boolean = false,
    @SerializedName("current_week") val currentWeek: Int = 1,
    @SerializedName("week_title") val weekTitle: String? = null,
    @SerializedName("week_goals") val weekGoals: List<String>? = emptyList()
)

// 3. 서랍 목록용 데이터 모델
data class SessionSummary(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("title") val title: String,
    @SerializedName("date") val date: String,
    @SerializedName("session_type") val sessionType: String = "GENERAL",
    @SerializedName("status") val status: String? = null
)