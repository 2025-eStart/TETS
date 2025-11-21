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

    // ★ 추가: 상담 제목 및 목표 (UI 표시용)
    private val _sessionTitle = MutableStateFlow("상담 로딩 중...")
    val sessionTitle: StateFlow<String> = _sessionTitle.asStateFlow()

    private val _sessionGoals = MutableStateFlow<List<String>>(emptyList())
    val sessionGoals: StateFlow<List<String>> = _sessionGoals.asStateFlow()

    init {
        // 화면 진입 시, 빈 메시지를 보내서 서버의 "첫 인사(GREETING)"를 유도하거나
        // 또는 저장된 대화 내역을 불러오는 로직이 필요합니다.
        // 여기서는 "서버에 접속했다"는 신호를 보내는 것으로 가정합니다.
        // (LangGraph 서버 로직상, nickname이 없으면 첫 메시지가 닉네임이 되므로 주의 필요)

        // 임시: 사용자가 먼저 말을 걸도록 하거나,
        // 서버에 "init" 같은 특수 커맨드를 보내는 방법도 있습니다.
        // 일단은 빈 리스트로 시작합니다.
    }

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
                        // 3. 응답 처리
                        _messages.value = _messages.value + chatTurn.assistantMessage

                        // 4. 메타 데이터 업데이트 (제목, 목표)
                        if (!chatTurn.weekTitle.isNullOrBlank()) {
                            _sessionTitle.value = "${chatTurn.currentWeek}주차: ${chatTurn.weekTitle}"
                        }

                        // weekGoals는 이제 List<String> (non-null)이므로 그냥 비어있는지만 체크
                        if (chatTurn.weekGoals.isNotEmpty()) {
                            _sessionGoals.value = chatTurn.weekGoals
                        }

                        if (chatTurn.isSessionEnded) {
                            _isSessionEnded.value = true
                        }
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
}
