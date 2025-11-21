// data.model.chat.ChatResponse
package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

data class LangGraphResponse(
    @SerializedName("values") val values: StateValues
)

// 서버의 state_types.py에 정의된 State와 매핑됩니다.
data class StateValues(
    @SerializedName("messages") val messages: List<MessageData>, // 대화 내역 전체
    @SerializedName("current_week") val currentWeek: Int = 1,
    @SerializedName("exit") val exit: Boolean = false,           // 목표 달성 여부
    @SerializedName("protocol") val protocol: ProtocolData? = null
)

data class ProtocolData(
    @SerializedName("title") val title: String? = "",
    @SerializedName("goals") val goals: List<String>? = emptyList()
)