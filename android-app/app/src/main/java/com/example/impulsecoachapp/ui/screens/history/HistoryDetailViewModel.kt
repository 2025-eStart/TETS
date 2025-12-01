// ui.screens.history.HistoryDetailViewModel.kt
package com.example.impulsecoachapp.ui.screens.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.model.chat.SessionSummary
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.domain.model.ChatMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
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

    init {
        // 화면 진입 시 한 번 과거 세션 목록도 불러오기
        loadHistoryList()
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

            // 💡 여기서는 서버에 새 세션을 강제로 시작만 해 두고,
            // 이 화면 자체의 메시지는 그대로 둔다.
            val result = repository.startSession(forceNew = true)

            result.onFailure { e ->
                _errorMessage.value = "새로운 상담을 시작하지 못했습니다: ${e.message}"
            }

            // 새 세션이 생겼으니 목록을 최신 상태로 갱신
            loadHistoryList()

            _isLoading.value = false
        }
    }
}
