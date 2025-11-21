//data.model.chat.ChatRequest

package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

data class LangGraphRequest(
    @SerializedName("input") val input: InputData,
    @SerializedName("config") val config: ConfigData? = null,
    @SerializedName("stream_mode") val streamMode: List<String> = listOf("values") // 결과를 한 번에 받기 위함
)

data class InputData(
    @SerializedName("messages") val messages: List<MessageData>
)

data class MessageData(
    @SerializedName("type") val type: String,   // "user"
    @SerializedName("content") val content: String
)

data class ConfigData(
    @SerializedName("configurable") val configurable: Map<String, String>? = null
)