package com.example.impulsecoachapp.data.model.chat

data class ChatResponse(
    val success: Boolean,
    val message: String,
    val data: ChatData
)

data class ChatData(
    val emotion: String,
    val spending: String,
    val action: String
)
