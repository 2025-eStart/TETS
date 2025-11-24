// ui.screens.chat.ChatViewModel
package com.example.impulsecoachapp.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val repository: ActualChatRepository
) : ViewModel() {

    // 1. 메시지 목록
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    // 2. 로딩 상태
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    // 3. 세션 종료 여부
    private val _isSessionEnded = MutableStateFlow(false)
    val isSessionEnded: StateFlow<Boolean> = _isSessionEnded.asStateFlow()

    // 4. 상담 메타데이터 (제목, 목표)
    private val _sessionTitle = MutableStateFlow("상담 준비 중...")
    val sessionTitle: StateFlow<String> = _sessionTitle.asStateFlow()

    private val _sessionGoals = MutableStateFlow<List<String>>(emptyList())
    val sessionGoals: StateFlow<List<String>> = _sessionGoals.asStateFlow()

    // 5. 현재 주차 (로딩 중일 땐 null)
    private val _currentWeek = MutableStateFlow<Int?>(null)
    val currentWeek: StateFlow<Int?> = _currentWeek.asStateFlow()

    // 6. 에러 메시지 (Toast용, 일회성 이벤트)
    private val _toastMessage = MutableStateFlow<String?>(null)
    val toastMessage: StateFlow<String?> = _toastMessage.asStateFlow()

    init {
        loadInitialMessage()
    }

    // 공통 함수(applyChatTurn) 재사용
    private fun loadInitialMessage() {
        viewModelScope.launch {
            _isLoading.value = true
            // startSession: 봇 깨우기(__init__) -> 첫 인사 받아오기
            val result = repository.startSession()

            result.onSuccess { turn ->
                // 성공 시: 공통 함수로 모든 상태(메시지, 제목, 목표, 주차) 한 방에 업데이트
                applyChatTurn(turn)
            }.onFailure {
                _messages.value = listOf(ChatMessage.GuideMessage("서버와 연결할 수 없습니다."))
            }
            _isLoading.value = false
        }
    }

    // 사용자가 메시지 전송 시
    fun sendMessage(text: String) {
        if (text.isBlank() || _isLoading.value) return

        // UI 즉시 반영 (낙관적 업데이트)
        val userMessage = ChatMessage.UserResponse(text)
        _messages.value = _messages.value + userMessage
        _isLoading.value = true

        viewModelScope.launch {
            val result = repository.sendChatMessage(text = text)

            result.onSuccess { turn ->
                applyChatTurn(turn)
            }.onFailure { error ->
                // 실패 시 에러 메시지 추가 (또는 UserResponse 제거 로직 등 추가 가능)
                _messages.value = _messages.value + ChatMessage.GuideMessage("오류: ${error.message}")
            }
            _isLoading.value = false
        }
    }

    // 새 세션 시작 (버튼 클릭 시)
    fun onNewSessionClick() {
        viewModelScope.launch {
            try {
                _isLoading.value = true

                // 1. 서버에 강제 리셋 요청
                val welcomeMessage = repository.startNewGeneralSession()

                // 2. UI 상태 초기화 (새 방이니까 싹 비움)
                _messages.value = listOf(ChatMessage.GuideMessage(welcomeMessage))
                _isSessionEnded.value = false
                _sessionTitle.value = "일반 상담" // 혹은 "로딩 중..."
                _sessionGoals.value = emptyList()
                // _currentWeek는 서버 응답에 따라 달라질 수 있으니 유지하거나 null 처리

            } catch (e: Exception) {
                _toastMessage.value = "세션 생성 실패: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    // ★ 핵심: 서버 응답(ChatTurn)을 UI 상태로 변환하는 '단일 진실 공급원(Source of Truth)'
    private fun applyChatTurn(chatTurn: ChatTurn) {
        // 1. 메시지 추가
        _messages.value = _messages.value + chatTurn.assistantMessage

        // 2. 주차 업데이트 (null -> 숫자)
        _currentWeek.value = chatTurn.currentWeek

        // 3. 제목/목표 업데이트 (값이 있을 때만)
        if (!chatTurn.weekTitle.isNullOrBlank()) {
            _sessionTitle.value = "${chatTurn.currentWeek}주차: ${chatTurn.weekTitle}"
        }
        if (chatTurn.weekGoals.isNotEmpty()) {
            _sessionGoals.value = chatTurn.weekGoals
        }

        // 4. 종료 여부
        if (chatTurn.isSessionEnded) {
            _isSessionEnded.value = true
        }
    }

    // Toast 메시지 보여준 후 닫기용
    fun clearToastMessage() {
        _toastMessage.value = null
    }
}
