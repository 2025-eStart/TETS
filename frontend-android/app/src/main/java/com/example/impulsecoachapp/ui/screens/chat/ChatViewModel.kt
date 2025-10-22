package com.example.impulsecoachapp.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.repository.ChatRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel // 1. Hilt ViewModel로 선언
class ChatViewModel @Inject constructor( // 2. 생성자에서 ChatRepository를 주입받음
    private val repository: ChatRepository
) : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    // 로딩 상태를 UI에 표시하기 위한 StateFlow
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    // 세션 종료 여부를 UI에 알리기 위한 StateFlow
    private val _isSessionEnded = MutableStateFlow(false)
    val isSessionEnded: StateFlow<Boolean> = _isSessionEnded.asStateFlow()

    init {
        // 초기 메시지 (기존과 동일)
        _messages.value = listOf(
            ChatMessage.GuideMessage("안녕! 나는 너의 소비 습관을 함께 돌아볼 임펄스 코치야. 오늘 어떤 일이 있었니?")
        )
    } // [수정] init { ... } 블록을 여기서 닫습니다.

    // 사용자의 자유 텍스트 입력을 처리하는 함수
    fun sendMessage(text: String) {
        if (text.isBlank() || _isLoading.value || _isSessionEnded.value) return

        // 1. 사용자의 메시지를 화면에 바로 표시
        val userMessage = ChatMessage.UserResponse(text)
        _messages.value = _messages.value + userMessage

        // 2. 로딩 시작
        _isLoading.value = true

        // 3. Repository(API)를 호출
        viewModelScope.launch {
            try {
                // 4. 새 함수 호출 및 반환값(Result) 처리
                val result = repository.sendChatMessage(text = text, endSession = false)

                result.fold(
                    onSuccess = { chatTurn ->
                        // 5. 성공: 봇의 응답(ChatTurn.assistantMessage)을 화면에 추가
                        _messages.value = _messages.value + chatTurn.assistantMessage

                        // 6. 세션 종료 여부 확인
                        if (chatTurn.isSessionEnded) {
                            _isSessionEnded.value = true
                            // (필요시) 숙제(chatTurn.homework) 처리 로직 추가
                        }
                    },
                    onFailure = { error ->
                        // 7. 실패: 에러 메시지를 GuideMessage로 표시
                        val errorMessage = ChatMessage.GuideMessage(
                            "오류가 발생했습니다: ${error.message}"
                        )
                        _messages.value = _messages.value + errorMessage
                    }
                )
            } finally {
                // 8. 로딩 종료
                _isLoading.value = false
            }
        }
    }

    // (옵션) 사용자가 명시적으로 세션을 종료할 때 호출하는 함수
    fun endCurrentSession(finalMessage: String = "상담을 종료합니다.") {
        if (_isLoading.value || _isSessionEnded.value) return

        val userMessage = ChatMessage.UserResponse(finalMessage)
        _messages.value = _messages.value + userMessage
        _isLoading.value = true

        viewModelScope.launch {
            try {
                // endSession = true로 호출
                val result = repository.sendChatMessage(text = finalMessage, endSession = true)

                result.fold(
                    onSuccess = { chatTurn ->
                        // 봇이 마지막 응답을 줄 경우
                        // [수정] chatTurn.assistantMessage는 ChatMessage 타입이므로,
                        // GuideMessage로 형변환(casting)해야 .text 속성에 접근할 수 있습니다.
                        val assistantMessage = chatTurn.assistantMessage
                        if (assistantMessage is ChatMessage.GuideMessage && assistantMessage.text.isNotBlank()) {
                            _messages.value = _messages.value + assistantMessage
                        }
                        _isSessionEnded.value = true // 세션 종료 확정
                    },
                    onFailure = { error ->
                        val errorMessage = ChatMessage.GuideMessage(
                            "세션 종료 중 오류: ${error.message}"
                        )
                        _messages.value = _messages.value + errorMessage
                    }
                )
            } finally {
                _isLoading.value = false
            }
        }
    }
}
