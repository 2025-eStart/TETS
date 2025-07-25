package com.example.impulsecoachapp.ui.screens.chat

import com.example.impulsecoachapp.model.chat.ChatMessage

class DummyChatRepository : ChatRepository {
    override suspend fun getNextMessage(userInput: String): ChatMessage {
        return when (userInput) {
            "네 있었어요" -> ChatMessage.GuideMessage("무슨 소비였는지 말해줄 수 있어?")
            "잘 모르겠어요" -> ChatMessage.GuideMessage("최근에 충동적이었다고 느낀 순간이 있을까?")
            else -> ChatMessage.GuideMessage("알겠어. 그럼 오늘 하루는 어땠는지부터 돌아볼까?")
        }
    }
}
