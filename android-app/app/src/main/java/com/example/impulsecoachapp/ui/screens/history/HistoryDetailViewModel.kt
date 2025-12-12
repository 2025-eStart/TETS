// ui.screens.history.HistoryDetailViewModel.kt
package com.example.impulsecoachapp.ui.screens.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.model.chat.SessionSummary
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.domain.model.ChatMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HistoryDetailViewModel @Inject constructor(
    private val repository: ActualChatRepository
) : ViewModel() {

    // 1. 화면에 보여줄 메시지 리스트 (채팅방과 동일한 타입!)
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    // 2. 로딩 상태
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    // 3. 에러 메시지
    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    // 4. 서랍에 사용할 과거 세션 목록
    private val _historyList = MutableStateFlow<List<SessionSummary>>(emptyList())
    val historyList: StateFlow<List<SessionSummary>> = _historyList.asStateFlow()

    // 5. 주간 상담 진행 중 여부 (버튼 잠금용)
    private val _isWeeklyModeLocked = MutableStateFlow(false)
    val isWeeklyModeLocked: StateFlow<Boolean> = _isWeeklyModeLocked.asStateFlow()

    // 6. 화면 이동 이벤트를 위한 SharedFlow (일회성 이벤트): 새 세션 생성 시 chatscreen으로 이동
    private val _navigateToChatEvent = MutableSharedFlow<Unit>()
    val navigateToChatEvent: SharedFlow<Unit> = _navigateToChatEvent.asSharedFlow()

    init {
        loadHistoryList() // 1. 화면 진입 시 한 번 과거 세션 목록도 불러오기
        checkCurrentSessionStatus() // 2. 현재 유저 상태(주간상담 중인지) 체크
    }

    // 현재 세션 상태 확인 함수 (새 세션 생성 버튼 잠금용)
    private fun checkCurrentSessionStatus() {
        viewModelScope.launch {
            // forceNew = false로 호출하여 현재 상태만 조회 (DB 변경 없이 status flag만 가져옴)
            val result = repository.initOrRestoreSession(forceNew = false)

            result.onSuccess { res ->
                // ChatViewModel과 동일한 로직 적용
                // 기본적으로 서버가 주는 isWeeklyInProgress를 따르지만,
                // 만약 현재 세션이 이미 '종료(ended)'된 상태라면 -> 새 세션을 만들 수 있게 잠금 해제
                if (res.status == "ended") {
                    _isWeeklyModeLocked.value = false
                } else {
                    _isWeeklyModeLocked.value = res.isWeeklyInProgress
                }
            }
            // 실패 시에는 기본값(false) 유지 혹은 에러 처리
        }
    }

    // 특정 threadId의 메시지 히스토리 로드 (기존 코드 유지)
    fun loadHistory(threadId: String) {
        viewModelScope.launch {
            _isLoading.value = true
            _errorMessage.value = null

            val result = repository.getSessionHistory(threadId)

            result.onSuccess { list ->
                _messages.value = list
            }.onFailure { e ->
                _errorMessage.value = "기록을 불러오지 못했습니다: ${e.message}"
            }

            _isLoading.value = false
        }
    }

    // 서랍에 뿌릴 세션 목록 로드
    fun loadHistoryList() {
        viewModelScope.launch {
            try {
                val result = repository.getHistoryList()
                result.onSuccess { list ->
                    _historyList.value = list
                }.onFailure { e ->
                    // 필요하면 에러 메시지로도 활용
                    _errorMessage.value = "과거 상담 목록을 불러오지 못했습니다: ${e.message}"
                }
            } catch (e: Exception) {
                _errorMessage.value = "과거 상담 목록을 불러오지 못했습니다: ${e.message}"
            }
        }
    }

    // "✨ 새로운 상담 시작하기" 클릭 시 동작
    fun onNewSessionClick() {
        viewModelScope.launch {
            _isLoading.value = true
            _errorMessage.value = null

            // 1. 서버에 강제 새 세션 생성 요청
            val result = repository.startSession(forceNew = true)

            result.onSuccess {
                // [추가] 성공하면 즉시 잠금 상태 해제 (UI 반영)
                _isWeeklyModeLocked.value = false

                // 2. ChatScreen으로 이동 이벤트 발생
                _navigateToChatEvent.emit(Unit)
            }.onFailure { e ->
                _errorMessage.value = "새 FAQ를 시작하지 못했습니다: ${e.message}"
            }

            // 새 세션이 생겼으니 목록을 최신 상태로 갱신
            loadHistoryList()
            _isLoading.value = false
        }
    }
}
