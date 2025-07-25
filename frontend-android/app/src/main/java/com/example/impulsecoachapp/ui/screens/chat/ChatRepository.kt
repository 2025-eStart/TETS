package com.example.impulsecoachapp.ui.screens.chat

import com.example.impulsecoachapp.model.chat.ChatMessage

interface ChatRepository {
    suspend fun getNextMessage(userInput: String): ChatMessage
}