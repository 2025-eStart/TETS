// ui.screens.ChatViewModel.kt
package com.example.impulsecoachapp.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.model.chat.SessionSummary
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlin.collections.plus

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

    // 7. 서랍에 들어갈 과거 기록 목록
    private val _historyList = MutableStateFlow<List<SessionSummary>>(emptyList())
    val historyList: StateFlow<List<SessionSummary>> = _historyList.asStateFlow()

    init {
        // 앱 켜질 때 1. 현재 방 접속, 2. 과거 기록 가져오기 둘 다 수행
        restoreSessionOrStartNew()
        loadHistoryList()
    }

    // 상황 1: 앱 켜질 때 (이어하기. 채팅 내역 그대로 남아 있음)
    private fun restoreSessionOrStartNew() {
        viewModelScope.launch {
            _isLoading.value = true

            // 1) 현재 진행 중인 threadId가 있는지 확인
            val threadId = repository.getCurrentThreadId()

            if (threadId != null) {
                // ✅ 이전에 진행 중이던 세션이 있다 → 서버에서 해당 스레드의 전체 로그를 가져온다
                val historyResult = repository.getSessionHistory(threadId)

                historyResult.onSuccess { list ->
                    // 전체 대화를 그대로 복원
                    _messages.value = list

                    // (옵션) 세션 메타데이터도 같이 복원하고 싶다면:
                    // - /sessions API에서 threadId 매칭해서 제목/주차/목표를 찾거나
                    // - getSessionHistory 응답에 메타데이터를 추가해서 받아오면 됨
                    // 여기서는 우선 메시지 복원만 처리

                }.onFailure { e ->
                    // 복원 실패 시: 안내 메시지 + 새 세션 시작으로 폴백
                    _messages.value = listOf(
                        ChatMessage.GuideMessage("이전 상담 내역을 불러오지 못했어요. 새로운 상담을 시작할게요.")
                    )
                    // 🔁 강제 새 세션 시작
                    processSessionStart(isReset = true)
                }

            } else {
                // ✅ 진행 중인 스레드가 없음 → 기존 로직대로 새 세션(or 기존 서버 세션) 시작
                processSessionStart(isReset = false)
            }

            _isLoading.value = false
        }
    }

    /* 과거 이어하기 함수
    private fun resumeSession() {
        viewModelScope.launch {
            _isLoading.value = true
            // forceNew = false : 기존 방 유지
            processSessionStart(isReset = false)
            _isLoading.value = false
        }
    }
    */

    // 상황 2: 버튼 눌렀을 때 (새로하기)
    fun onNewSessionClick() {
        viewModelScope.launch {
            _isLoading.value = true

            // 1. 화면 비우기
            _messages.value = emptyList()
            _sessionTitle.value = "새로운 상담"

            // 2. 강제 새 방 배정 (forceNew=true)
            // 내부적으로 repository.startSession(true) 호출
            processSessionStart(isReset = true)

            // 3. ★ [핵심] 서랍 목록 새로고침!
            // (방금 끝난 대화가 서랍으로 들어가야 하니까)
            loadHistoryList()

            _isLoading.value = false
        }
    }

    // ★ 공통 로직 (Private Helper): 실제로 서버를 찌르는 역할
    private suspend fun processSessionStart(isReset: Boolean) {
        // Repository 하나만 호출하면 됨 (로직 중복 제거)
        val result = repository.startSession(forceNew = isReset)

        result.onSuccess { turn ->
            applyChatTurn(turn)
        }.onFailure {
            _messages.value = listOf(ChatMessage.GuideMessage("연결 실패"))
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

    // ★ 핵심: 서버 응답(ChatTurn)을 UI 상태로 변환하는 '단일 진실 공급원(Source of Truth)'
    private fun applyChatTurn(chatTurn: ChatTurn) {
        // 1. 메시지 추가
        _messages.value = _messages.value + chatTurn.assistantMessage

        // 2. 주차 업데이트 (null -> 숫자)
        _currentWeek.value = chatTurn.currentWeek

        // 3. 주차 업데이트 (값이 있을 때만)
        if (!chatTurn.weekTitle.isNullOrBlank()) {
            _sessionTitle.value = "${chatTurn.currentWeek}주차 상담"
        }
        if (chatTurn.weekGoals.isNotEmpty()) {
            _sessionGoals.value = chatTurn.weekGoals
        }

        // 4. 종료 여부
        if (chatTurn.isSessionEnded) {
            _isSessionEnded.value = true
        }
    }

    // 과거 기록 가져오는 함수
    private fun loadHistoryList() {
        viewModelScope.launch {
            // repository.getSessions()는 서버 /sessions/{id} 호출
            val result = repository.getHistoryList()
            result.onSuccess { list ->
                _historyList.value = list
            }
        }
    }

    // Toast 메시지 보여준 후 닫기용
    fun clearToastMessage() {
        _toastMessage.value = null
    }
}