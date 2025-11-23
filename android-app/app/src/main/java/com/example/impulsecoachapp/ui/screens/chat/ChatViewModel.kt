// ui.screens.chat.ChatViewModel
package com.example.impulsecoachapp.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val repository: ChatRepository
) : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _isSessionEnded = MutableStateFlow(false)
    val isSessionEnded: StateFlow<Boolean> = _isSessionEnded.asStateFlow()

    // 상담 제목 및 목표 (UI 표시용)
    private val _sessionTitle = MutableStateFlow("상담 준비 중...")
    val sessionTitle: StateFlow<String> = _sessionTitle.asStateFlow()

    private val _sessionGoals = MutableStateFlow<List<String>>(emptyList())
    val sessionGoals: StateFlow<List<String>> = _sessionGoals.asStateFlow()

    /**
     * 화면 진입 시 한 번만 호출:
     * - 서버에 "빈 신호"를 보내서 첫 턴(닉네임 안내/인사말)을 서버가 생성하게 함
     * - 이미 메시지가 있거나 로딩 중이면 아무 것도 안 함 (재진입 방지)
     */
    fun startSessionIfNeeded() {
        if (_messages.value.isNotEmpty() || _isLoading.value) return

        _isLoading.value = true

        viewModelScope.launch {
            try {
                // text = "" 이 "빈 신호" 역할 (서버에서 nickname 없으면 닉네임 안내로 응답하도록 설계)
                val result = repository.sendChatMessage(text = "", endSession = false)

                result.fold(
                    onSuccess = { chatTurn ->
                        applyChatTurn(chatTurn)
                    },
                    onFailure = { error ->
                        _messages.value = _messages.value + ChatMessage.GuideMessage(
                            "서버 연결 오류: ${error.message}"
                        )
                    }
                )
            } finally {
                _isLoading.value = false
            }
        }
    }

    /**
     * 사용자가 채팅창에 입력했을 때 호출되는 함수
     */
    fun sendMessage(text: String) {
        if (text.isBlank() || _isLoading.value) return

        // 1. 사용자 메시지 추가
        val userMessage = ChatMessage.UserResponse(text)
        _messages.value = _messages.value + userMessage
        _isLoading.value = true

        viewModelScope.launch {
            try {
                // 2. API 호출
                val result = repository.sendChatMessage(text = text, endSession = false)

                result.fold(
                    onSuccess = { chatTurn ->
                        // 3. 서버 응답 반영
                        applyChatTurn(chatTurn)
                    },
                    onFailure = { error ->
                        _messages.value = _messages.value + ChatMessage.GuideMessage(
                            "서버 연결 오류: ${error.message}"
                        )
                    }
                )
            } finally {
                _isLoading.value = false
            }
        }
    }

    /**
     * 서버에서 내려온 ChatTurn을 ViewModel 상태에 반영하는 공통 함수
     */
    private fun applyChatTurn(chatTurn: ChatTurn) {
        // 1) 봇 메시지 추가
        _messages.value = _messages.value + chatTurn.assistantMessage

        // 2) 메타데이터(주차/제목/목표) 업데이트
        if (!chatTurn.weekTitle.isNullOrBlank()) {
            _sessionTitle.value = "${chatTurn.currentWeek}주차: ${chatTurn.weekTitle}"
        }

        if (chatTurn.weekGoals.isNotEmpty()) {
            _sessionGoals.value = chatTurn.weekGoals
        }

        // 3) 세션 종료 여부
        if (chatTurn.isSessionEnded) {
            _isSessionEnded.value = true
        }
    }
}
