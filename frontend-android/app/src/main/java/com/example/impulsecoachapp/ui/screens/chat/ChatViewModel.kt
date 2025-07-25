package com.example.impulsecoachapp.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.model.chat.ChatMessage
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class ChatViewModel(
    private val repository: ChatRepository = ActualChatRepository() // actual or dummychat, 추후에는 Hilt 같은 의존성 주입으로 더 우아하게 관리할 수 있다
) : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages

    init {
        // [수정] 초기 메시지를 선택지 대신 개방형 질문으로 변경
        _messages.value = listOf(
            ChatMessage.GuideMessage("안녕! 나는 너의 소비 습관을 함께 돌아볼 임펄스 코치야. 오늘 어떤 일이 있었니?")
        )
    }

    // 기존 선택지 처리 함수
    fun handleUserSelection(option: String) {
        val userMessage = ChatMessage.UserResponse(option)
        _messages.value = _messages.value + userMessage

        viewModelScope.launch {
            val botReply = repository.getNextMessage(option)
            _messages.value = _messages.value + botReply
        }
    }

    // [추가] 사용자의 자유 텍스트 입력을 처리하는 함수
    fun sendMessage(text: String) {
        if (text.isBlank()) return

        // 1. 사용자의 메시지를 화면에 바로 표시
        val userMessage = ChatMessage.UserResponse(text)
        _messages.value = _messages.value + userMessage

        // 2. Repository(API)를 호출하여 봇의 응답을 받음
        viewModelScope.launch {
            val botReply = repository.getNextMessage(text)
            // 3. 봇의 응답을 화면에 추가
            _messages.value = _messages.value + botReply
        }
    }
}

/*
// ViewModel에 실제 Repository 주입
// 나중에는 Hilt나 Koin 같은 의존성 주입 라이브러리를 사용해서
// ChatViewModel에 DummyChatRepository 대신 ActualChatRepository를 주입하게 됩니다.
// ChatViewModel 생성자
class ChatViewModel(
    // 의존성 주입을 통해 실제 Repository를 받음
    private val repository: ChatRepository = ActualChatRepository()
) : ViewModel() {
    // ...
}
 */