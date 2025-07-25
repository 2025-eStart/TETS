package com.example.impulsecoachapp.model.chat

sealed class ChatMessage {
    data class GuideMessage(val text: String) : ChatMessage()
    data class UserResponse(val text: String) : ChatMessage()
    data class ChoiceMessage(val options: List<String>) : ChatMessage()
}
