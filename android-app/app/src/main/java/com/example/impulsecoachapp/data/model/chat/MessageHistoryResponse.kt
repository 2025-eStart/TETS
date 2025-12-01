// MessageHistoryResponse.kt
package com.example.impulsecoachapp.data.model.chat

import com.google.gson.annotations.SerializedName

class MessageHistoryResponse (
    @SerializedName("role") val role: String, // "user" or "assistant"
    @SerializedName("text") val text: String,
    @SerializedName("created_at") val createdAt: String?
)