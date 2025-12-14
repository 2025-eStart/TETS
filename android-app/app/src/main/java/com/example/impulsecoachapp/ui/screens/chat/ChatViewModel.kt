// ui.screens.ChatViewModel.kt
package com.example.impulsecoachapp.ui.screens.chat

import android.media.Image
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.model.chat.SessionSummary
import com.example.impulsecoachapp.data.model.chat.InitSessionResponse
import com.example.impulsecoachapp.data.model.chat.ResetRequest
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
import androidx.lifecycle.SavedStateHandle
import com.example.impulsecoachapp.R

import com.example.impulsecoachapp.ui.screens.chat.ChatViewModel.LoadingStage

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val repository: ActualChatRepository,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {

    /* 클래스 정의 */
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
    private val _loadingStage = MutableStateFlow<LoadingStage?>(null)
    val loadingStage: StateFlow<LoadingStage?> = _loadingStage.asStateFlow()

    // 9. 주간 상담 진행 중 여부 (버튼 잠금용)
    private val _isWeeklyModeLocked = MutableStateFlow(false)
    val isWeeklyModeLocked: StateFlow<Boolean> = _isWeeklyModeLocked.asStateFlow()

    // 10. 현재 세션 타입 기억 변수
    private var currentSessionType: String = "WEEKLY" //기본값 WEEKLY

    // 11. 초기화 버튼 눌렀을 때 경고 팝업
    private val _showResetDialog = MutableStateFlow(false)
    val showResetDialog: StateFlow<Boolean> = _showResetDialog.asStateFlow()

    // LoadingStage Enum
    enum class LoadingStage {
        THINKING,      // 입력을 읽는 중
        SELECTING,     // 기법을 고르는 중
        APPLYING       // 기법을 적용해서 답변 조합 중
    }


    init { // 앱 켜질 때
        // 1. 네비게이션으로 전달받은 threadId가 있는지 확인
        val targetThreadId = savedStateHandle.get<String>("threadId")

        if (targetThreadId != null) {
            // [CASE A] 특정 세션 이어하기 (GENERAL)
            loadSpecificSession(targetThreadId)
        } else {
            // [CASE B] 평소처럼 앱 실행 (최신 상태 로드)
            restoreSessionOrStartNew()
        }
        loadHistoryList()
    }

    /* 함수 정의 */
    // 1. 특정 세션(General)을 로드하여 이어하기 모드로 설정
    fun loadSpecificSession(threadId: String) {
        viewModelScope.launch {
            _isLoading.value = true

            // 1. 목록(캐시)에서 세션 정보 찾기
            val foundSession = _historyList.value.find { it.sessionId == threadId }
            val dateStr = foundSession?.date

            // 2. 찾은 세션의 status를 보고 즉시 UI 잠금 여부 결정
            //    status가 "ended"이면 true, 아니면(null 포함) false
            _isSessionEnded.value = (foundSession?.status == "ended")

            currentSessionType = "GENERAL"
            repository.updateCurrentSessionInfo(threadId, currentSessionType)

            // 3. 메시지 내역 불러오기
            val historyResult = repository.getSessionHistory(threadId)
            _sessionTitle.value = "불러오는 중..."

            historyResult.onSuccess { history ->
                _messages.value = history
                if (dateStr != null) {
                    _sessionTitle.value = "FAQ ($dateStr)"
                } else {
                    _sessionTitle.value = "FAQ"
                }
                // 이어하기 모드이므로 새로운 세션 생성 버튼 잠금 해제
                _isWeeklyModeLocked.value = false
            }.onFailure {
                _messages.value = listOf(ChatMessage.GuideMessage("대화 내용을 불러오지 못했습니다."))
            }

            _isLoading.value = false
        }
    }

    // 2. 상황 1: 앱 켜질 때 (이어하기)
    private fun restoreSessionOrStartNew() {
        viewModelScope.launch {
            _isLoading.value = true
            _isSessionEnded.value = false // 일단 리셋

            // 1) 서버에게 현재 세션/스레드 상태 물어보기
            val initResult = repository.initOrRestoreSession(forceNew = false)

            initResult.onSuccess { initRes ->
                val threadId = initRes.threadId

                // 서버가 알려준 상태 즉시 반영
                // status가 "ended"이면 true, 그 외(null, "active")면 false
                // 이렇게 하면 히스토리를 로딩하기 전부터 입력창이 잠깁니다.
                if (initRes.status == "ended") {
                    _isSessionEnded.value = true
                }

                // (기존 로직)
                currentSessionType = initRes.sessionType
                _isWeeklyModeLocked.value = initRes.isWeeklyInProgress

                // [수정] 타이틀 결정 로직 (서랍 목록과 통일성 유지)
                _sessionTitle.value = if (initRes.sessionType == "WEEKLY") {
                    "${initRes.currentWeek}주차 상담"
                } else {
                    // GENERAL일 경우: "FAQ | {서버가 준 날짜}"
                    // initRes.createdAt은 이미 "YY-MM-DD HH:MM" 형태임
                    if (initRes.createdAt.isNullOrBlank()) {
                        "FAQ | ${initRes.createdAt}"
                    } else {
                        "FAQ" // fallback
                    }
                }

                // 2) 해당 스레드의 과거 메시지 전체 가져오기
                val historyResult = repository.getSessionHistory(threadId)

                historyResult.onSuccess { history ->
                    if (history.isNotEmpty()) {
                        // 과거 대화가 있으면 복원
                        _messages.value = history
                    } else {
                        // 히스토리가 없으면 첫 인사
                        // [중요] 단, 이미 종료된 세션이라면 굳이 startSession을 불러서 봇을 깨울 필요 없음
                        if (!_isSessionEnded.value) {
                            startInitialSession()
                        }
                    }
                }.onFailure {
                    // 히스토리 로드 실패 시 재시도 (종료 안 된 경우만)
                    if (!_isSessionEnded.value) {
                        startInitialSession()
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

    // 3. 상황 2: 버튼 눌렀을 때 (새로하기)
    fun onNewSessionClick() {
        viewModelScope.launch {
            _isLoading.value = true

            // 1. 화면 비우기 & 상태 리셋
            _messages.value = emptyList()
            _sessionTitle.value = "새 FAQ"
            _isSessionEnded.value = false
            _isWeeklyModeLocked.value = false // 새 세션 생성 버튼 잠금 해제

            // 2. 강제 새 방 배정 (기존 processSessionStart 내용을 여기서 직접 수행)
            val result = repository.startSession(forceNew = true)

            result.onSuccess { turn ->
                // 2-1. 첫 봇 메시지(채팅 턴) 화면에 반영
                applyChatTurn(turn)

                // [핵심 추가 로직] 3. 목록 새로고침 후 제목 업데이트
                // 새 세션이 생겼으니 서랍 목록을 갱신합니다.
                val historyRefresh = repository.getHistoryList()
                historyRefresh.onSuccess { list ->
                    _historyList.value = list

                    // 방금 만든 세션(현재 threadId와 일치하는 것)을 찾아 제목을 업데이트
                    val currentThreadId = repository.getCurrentThreadId()
                    val mySession = list.find { it.sessionId == currentThreadId }

                    if (mySession != null) {
                        // 서버가 준 "FAQ | 25-12-13 15:40" 형태의 제목 적용
                        _sessionTitle.value = mySession.title
                    }
                }
            }.onFailure {
                _messages.value = listOf(ChatMessage.GuideMessage("연결 실패"))
            }

            // 3. 서랍 목록 새로고침 (방금 끝난 대화가 서랍으로 들어가야 함)
            loadHistoryList()
            _isLoading.value = false
        }
    }

    // 4. 실제로 서버를 찌르는 역할
    private suspend fun processSessionStart(isReset: Boolean) {
        val result = repository.startSession(forceNew = isReset)

        result.onSuccess { turn -> applyChatTurn(turn) }
            .onFailure { _messages.value = listOf(ChatMessage.GuideMessage("연결 실패"))}
    }

    // 5. 로딩 스테이지 표시용 타이머
    private fun startLoadingStageTimer() {
        // GENERAL 상담이면 바로 APPLYING 단계로 건너뜀
        if (currentSessionType == "GENERAL") {
            _loadingStage.value = LoadingStage.THINKING
            return // 여기서 함수 종료 (타이머 실행 안 함)
        }

        // WEEKLY 상담일 때만 단계별 로딩 표시
        _loadingStage.value = LoadingStage.THINKING

        viewModelScope.launch {
            kotlinx.coroutines.delay(50000)
            if (_isLoading.value) _loadingStage.value = LoadingStage.SELECTING

            kotlinx.coroutines.delay(35000)
            if (_isLoading.value) _loadingStage.value = LoadingStage.APPLYING
        }
    }

    // 6. 사용자가 메시지 전송 시
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
                _messages.value = _messages.value + ChatMessage.GuideMessage("오류가 발생했어요! 조금 뒤에 다시 답변을 보내주세요@: ${error.message}")
            }
            _isLoading.value = false
            _loadingStage.value = null // 끝나면 스테이지 리셋
        }
    }

    // 7. 서버 응답(ChatTurn)을 UI 상태로 변환하는 Source of Truth
    private fun applyChatTurn(chatTurn: ChatTurn) {
        // 1. 메시지 추가
        _messages.value = _messages.value + chatTurn.assistantMessage

        // 2-1. 주차 업데이트 (null -> 숫자)
        _currentWeek.value = chatTurn.currentWeek
        // 2-2. 주차 업데이트
        if (!chatTurn.weekTitle.isNullOrBlank()) {
            if (currentSessionType == "WEEKLY") {
                _sessionTitle.value = "${chatTurn.currentWeek}주차 상담"
            } else {

                _sessionTitle.value = "FAQ"
            }
        }
        // 3. 종료 여부 확인 및 버튼 잠금 해제 로직
        if (chatTurn.isSessionEnded) {
            _isSessionEnded.value = true
            _isWeeklyModeLocked.value = false // 상담이 끝났으므로 "새 세션 만들기" 버튼 잠금 해제

            loadHistoryList()

            // 10주차 주간상담 종료 시 초기화 버튼 안내 추가
            if (currentSessionType == "WEEKLY" && chatTurn.currentWeek == 10) {
                viewModelScope.launch {
                    _messages.value = _messages.value + ChatMessage.GuideMessage(
                        "상단 바 오른쪽의 초기화 버튼을 누르면 상담 프로그램이 초기화돼요!" +
                                "\n(기존 상담 내역은 서랍에서 계속 접근 가능해요🦊)"
                    )
                    kotlinx.coroutines.delay(2000)
                    _messages.value = _messages.value + ChatMessage.GuideMessage(
                        "초기화 버튼을 누르는 즉시 새로운 1주차 상담이 시작되니, 새로운 상담이 필요할 때 눌러주세요!"
                    )
                    kotlinx.coroutines.delay(2000)
                    _messages.value = _messages.value + ChatMessage.GuideMessage(
                        "일반 상담을 통해서 언제든 궁금한 것을 물어보실 수 있어요 🦊"
                    )
                }
            }
        }
    }

    // 8. 과거 기록 가져오기
    private fun loadHistoryList() {
        viewModelScope.launch {
            // repository.getSessions()는 서버 /sessions/{id} 호출
            val result = repository.getHistoryList()
            result.onSuccess { list ->
                _historyList.value = list
            }
        }
    }

    // 9. 상담 프로그램 완료 후 초기화
    fun resetSession() {
        viewModelScope.launch {
            if (_isLoading.value) return@launch
            _isLoading.value = true
            _isSessionEnded.value = false
            _loadingStage.value = null

            val result = repository.resetSession()

            result.onSuccess { initResponse ->
                // 1) 새 thread / 상태 반영 + displayMessage를 Guide로 먼저 보여줌
                applySessionState(initResponse)

                // 2) 그 다음 "__init__"로 1주차 첫 멘트 받아오기
                val firstTurnResult = repository.startSession(forceNew = false)
                firstTurnResult.onSuccess { turn ->
                    applyChatTurn(turn)
                }.onFailure { e ->
                    _messages.value = _messages.value + ChatMessage.GuideMessage(
                        "초기화 후 상담을 시작하는 중 오류가 발생했어요: ${e.message}"
                    )
                }

            }.onFailure { error ->
                _messages.value = _messages.value + ChatMessage.GuideMessage("초기화 실패: ${error.message}")
            }

            _isLoading.value = false
        }
    }

    // 10. 초기화 버튼 눌렀을 때 경고 팝업
    fun onResetButtonClick() {
        _showResetDialog.value = true
    }

    fun onDismissResetDialog() {
        _showResetDialog.value = false
    }

    fun onConfirmResetDialog() {
        _showResetDialog.value = false
        resetSession() // 여기서만 실제 리셋 실행
    }

    /*
    // Toast 메시지 보여준 후 닫기용
    fun clearToastMessage() {
        _toastMessage.value = null
    }
    */

    //////////// helper 함수 ////////////////

    // 2. restoreSessionOrStartNew 헬퍼
    private suspend fun startInitialSession() {
        val firstTurnResult = repository.startSession(forceNew = false)

        firstTurnResult.onSuccess { turn ->
            applyChatTurn(turn)
        }.onFailure {
            _messages.value = listOf(
                ChatMessage.GuideMessage("상담을 시작하는 중 오류가 발생했어요.")
            )
        }
    }

    // 9. resetSession 헬퍼
    private fun applySessionState(state: InitSessionResponse) {
        // 1. Repository의 현재 스레드 정보 갱신 (중요: 이후 메시지는 이 threadId로 전송됨)
        repository.updateCurrentSessionInfo(state.threadId, state.sessionType)
        currentSessionType = state.sessionType

        // 2. UI 상태 값 갱신 (주차, 타이틀)
        _currentWeek.value = state.currentWeek

        _sessionTitle.value = if (state.sessionType == "WEEKLY") {
            "${state.currentWeek}주차 상담"
        } else {
            // created_at이 있으면 날짜 표시, 없으면 그냥 FAQ
            if (state.createdAt.isNullOrBlank()) "FAQ | ${state.createdAt}" else "FAQ"
        }

        // 3. 잠금 상태 동기화
        // status가 "ended"면 입력창 잠금
        _isSessionEnded.value = (state.status == "ended")
        // 주간 상담 진행 중 여부에 따라 "새 세션 만들기" 버튼 잠금
        _isWeeklyModeLocked.value = state.isWeeklyInProgress

        // 4. 메시지 창 처리
        // 리셋 직후에는 새로운 세션 열고 안내 메시지(displayMessage)만 보여주기
        val guide = state.displayMessage.takeIf { it.isNotBlank() }
            ?: "상담이 초기화되었습니다. 1주차부터 다시 시작합니다."
        _messages.value = listOf(ChatMessage.GuideMessage(guide))

        // 5. 서랍(History) 목록 갱신 (리셋되면서 과거 기록이 아카이빙 되었을 것이므로)
        loadHistoryList()
    }

}

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