// ui.screens.ChatViewModel.kt
package com.example.impulsecoachapp.ui.screens.chat

import android.media.Image
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
import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.impulsecoachapp.R

import com.example.impulsecoachapp.ui.screens.chat.ChatViewModel.LoadingStage

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

    // 8. 로딩 스테이지 (메시지 기다릴 때)
    enum class LoadingStage {
        THINKING,      // 입력을 읽는 중
        SELECTING,     // 기법을 고르는 중
        APPLYING       // 기법을 적용해서 답변 조합 중
    }
    private val _loadingStage = MutableStateFlow<LoadingStage?>(null)
    val loadingStage: StateFlow<LoadingStage?> = _loadingStage.asStateFlow()


    init {
        // 앱 켜질 때 1. 현재 방 접속, 2. 과거 기록 가져오기 둘 다 수행
        restoreSessionOrStartNew()
        loadHistoryList()
    }

    // 상황 1: 앱 켜질 때 (이어하기. 채팅 내역 그대로 남아 있음)
    private fun restoreSessionOrStartNew() {
        viewModelScope.launch {
            _isLoading.value = true

            // 1) 서버에게 현재 세션/스레드 상태 물어보기
            val initResult = repository.initOrRestoreSession(forceNew = false)

            initResult.onSuccess { initRes ->
                val threadId = initRes.threadId

                // (선택) 상단 타이틀 업데이트
                _currentWeek.value = initRes.currentWeek
                _sessionTitle.value = when (initRes.sessionType) {
                    "WEEKLY" -> "${initRes.currentWeek}주차 상담"
                    else -> "일반 상담"
                }

                // 2) 해당 스레드의 과거 메시지 전체 가져오기
                val historyResult = repository.getSessionHistory(threadId)

                historyResult.onSuccess { history ->
                    if (history.isNotEmpty()) {
                        // ✅ [핵심] 과거 대화가 존재하는 경우:
                        //    → 그 대화만 화면에 복원하고, __init__ 안 보냄
                        _messages.value = history

                        // 여기서는 “AI가 이미 질문을 던졌고, 사용자가 아직 답 안 한 상태”를
                        // 포함해서, 어떤 경우든 "대화는 이미 시작된 상태"라고 보고
                        // 추가 init 호출 없이 사용자가 바로 이어서 입력하게 둔다.

                    } else {
                        // ✅ 완전히 새로운 세션(히스토리 없음) → 기존처럼 첫 인사 받기
                        val firstTurnResult = repository.startSession(forceNew = false)

                        firstTurnResult.onSuccess { turn ->
                            applyChatTurn(turn)
                        }.onFailure {
                            _messages.value = listOf(
                                ChatMessage.GuideMessage("상담을 시작하는 중 오류가 발생했어요.")
                            )
                        }
                    }
                }.onFailure {
                    // 히스토리 로드 실패 시에도 최소한 첫 턴은 띄워주기
                    val firstTurnResult = repository.startSession(forceNew = false)

                    firstTurnResult.onSuccess { turn ->
                        applyChatTurn(turn)
                    }.onFailure {
                        _messages.value = listOf(
                            ChatMessage.GuideMessage("상담을 시작하는 중 오류가 발생했어요.")
                        )
                    }
                }
            }.onFailure {
                _messages.value = listOf(
                    ChatMessage.GuideMessage("세션 정보를 가져오지 못했어요. 잠시 후 다시 시도해 주세요.")
                )
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
            _sessionTitle.value = "새 FAQ"

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

    // 로딩 스테이지 표시용 타이머
    private fun startLoadingStageTimer() {
        _loadingStage.value = LoadingStage.THINKING

        viewModelScope.launch {
            kotlinx.coroutines.delay(6000)
            if (_isLoading.value) _loadingStage.value = LoadingStage.SELECTING

            kotlinx.coroutines.delay(23000)
            if (_isLoading.value) _loadingStage.value = LoadingStage.APPLYING
        }
    }


    // 사용자가 메시지 전송 시
    fun sendMessage(text: String) {
        if (text.isBlank() || _isLoading.value) return

        // ✅ "__init__"일 때는 UI에 유저 버블 추가하지 않기
        val isInitCommand = text.trim() == "__init__"

        if (!isInitCommand) {
            // UI 즉시 반영 (낙관적 업데이트)
            val userMessage = ChatMessage.UserResponse(text)
            _messages.value = _messages.value + userMessage
        }

        _isLoading.value = true
        // 💡 로딩 단계 타이머 시작
        startLoadingStageTimer()

        viewModelScope.launch {
            val result = repository.sendChatMessage(text = text)

            result.onSuccess { turn ->
                applyChatTurn(turn)
            }.onFailure { error ->
                // 실패 시 에러 메시지 추가 (또는 UserResponse 제거 로직 등 추가 가능)
                _messages.value = _messages.value + ChatMessage.GuideMessage("오류: ${error.message}")
            }
            _isLoading.value = false
            _loadingStage.value = null // 끝나면 스테이지 리셋
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

// ChatScreen.kt 파일 하단이나 ChatBubble 근처에 추가

@Composable
fun GeneratingBubble(loadingStage: LoadingStage?) {
    val infiniteTransition = rememberInfiniteTransition(label = "loading")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    val text = when (loadingStage) {
        LoadingStage.THINKING ->
            "루시가 여행자님의 말을 곰곰이 되새기고 있어요…🦊"
        LoadingStage.SELECTING ->
            "어떤 기법이 지금 가장 도움이 될지 고르는 중이에요…"
        LoadingStage.APPLYING ->
            "선택한 기법으로 답변을 정리하고 있어요…"
        null ->
            "루시가 여행자님을 위해서 열심히 고민하는 중이에요! 조금만 기다려 주세요🦊"
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        horizontalArrangement = Arrangement.Start
    ) {
        // 봇 아이콘 (기존 ChatBubble과 일관성 유지)
        Image(
            painter = painterResource(id = R.drawable.ic_chatbot),
            contentDescription = "Generating",
            modifier = Modifier
                .size(28.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))

        // 텍스트
        Text(
            text = text,
            fontSize = 14.sp,
            color = Color.Gray,
            modifier = Modifier
                .align(Alignment.CenterVertically)
                .alpha(alpha) // 글자 투명도 애니메이션 적용
        )
    }
}