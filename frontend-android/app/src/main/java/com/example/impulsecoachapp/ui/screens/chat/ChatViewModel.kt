package com.example.impulsecoachapp.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.model.chat.ChatMessage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlin.collections.toMutableList

class ChatViewModel(
    private val repository: ChatRepository = DummyChatRepository() // 나중에 실제 구현체로 교체
) : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages

    init {
        // 초기 메시지 세팅
        _messages.value = listOf(
            ChatMessage.GuideMessage("안녕! 오늘 있었던 소비 중 기억에 남는 게 있어?"),
            ChatMessage.ChoiceMessage(listOf("네 있었어요", "잘 모르겠어요", "없어요"))
        )
    }

    fun handleUserSelection(option: String) {
        val current = _messages.value.toMutableList()
        current.add(ChatMessage.UserResponse(option))
        _messages.value = current

        // GPT 호출 또는 시나리오에 따른 응답 추가
        viewModelScope.launch {
            val botReply = repository.getNextMessage(option)
            _messages.value = _messages.value + botReply
        }
    }
}
