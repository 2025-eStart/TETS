//ui.screens.ChatScreen.kt
package com.example.impulsecoachapp.ui.screens.chat

import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.impulsecoachapp.R
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold
import kotlinx.coroutines.launch
import com.example.impulsecoachapp.ui.screens.chat.ChatViewModel.LoadingStage


@Composable
fun ChatScreen(
    targetThreadId: String?,
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    onBackPressed: () -> Unit,
    onOpenHistory: (String) -> Unit,          // 과거 채팅 threadId 넘겨줄 콜백
    onOpenChat: (String) -> Unit,
    viewModel: ChatViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val isSessionEnded by viewModel.isSessionEnded.collectAsState()
    val sessionTitle by viewModel.sessionTitle.collectAsState()
    val sessionGoals by viewModel.sessionGoals.collectAsState()
    val historyList by viewModel.historyList.collectAsState()
    val loadingStage by viewModel.loadingStage.collectAsState() // 로딩 문구

    val isWeeklyModeLocked by viewModel.isWeeklyModeLocked.collectAsState()  // 새 세션 생성 버튼 잠금 상태 구독

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed) // 서랍 상태 관리 변수
    val scope = rememberCoroutineScope()

    val context = LocalContext.current // Toast 띄우기 위한 Context

    // 네비게이션에서 넘어온 인자가 변경되면 ViewModel 데이터를 다시 로드해야 할 수도 있음
    // (하지만 ViewModel init에서 처리하므로, ChatScreen이 완전히 새로 그려질 땐 괜찮음.
    //  만약 이미 ChatScreen이 떠있는 상태에서 인자만 바뀌면 LaunchedEffect 필요)
    LaunchedEffect(targetThreadId) {
        if (targetThreadId != null) {
            viewModel.loadSpecificSession(targetThreadId)
        }
    }

    ModalNavigationDrawer(
        drawerState = drawerState, // 상태 연결 필수
        drawerContent = {
            ModalDrawerSheet {
                Text(
                    text = "지난 대화 & 새 채팅",
                    modifier = Modifier.padding(16.dp),
                    style = MaterialTheme.typography.titleMedium
                )
                HorizontalDivider()

                // [NEW CHAT 버튼]
                NavigationDrawerItem(
                    label = { Text(
                        text = if (isWeeklyModeLocked) "✨ 새 FAQ 시작하기 (🔒)" else "✨ 새 FAQ 시작하기",
                        // 잠겨있으면 회색, 아니면 기본색
                        color = if (isWeeklyModeLocked) Color.Gray else MaterialTheme.colorScheme.onSurface
                        )
                    },
                    selected = false,
                    onClick = {
                        // 세션 생성 버튼 잠금 상태 체크
                        if (isWeeklyModeLocked) {
                            Toast.makeText(context, "현재 진행 중인 주간 상담을 먼저 마무리해 주세요!", Toast.LENGTH_SHORT)
                                .show()
                        }else {
                            viewModel.onNewSessionClick()
                            scope.launch { drawerState.close() } // 클릭 후 서랍 닫기
                        }
                    }
                )

                HorizontalDivider()

                // [과거 기록 리스트]
                LazyColumn {
                    items(historyList) { session ->
                        NavigationDrawerItem(
                            label = { Text(session.title) },
                            badge = { Text(session.date) },
                            selected = false,
                            onClick = {
                                if (session.sessionType == "GENERAL") {
                                    // General -> 채팅방 열어서 이어하기
                                    onOpenChat(session.sessionId)
                                } else {
                                    // Weekly -> 읽기 전용 히스토리 화면
                                    onOpenHistory(session.sessionId)
                                }
                                scope.launch { drawerState.close() }
                            }
                        )
                    }
                }
            }
        }
    ) {
        ScreenScaffold(
            selectedTab = selectedTab,
            onTabSelected = onTabSelected
        ) { innerPadding ->
            ChatScreenContent(
                modifier = Modifier,
                innerPadding = innerPadding,
                messages = messages,
                isLoading = isLoading,
                loadingStage = loadingStage,
                isSessionEnded = isSessionEnded,
                sessionTitle = sessionTitle,
                sessionGoals = sessionGoals,
                onSendMessage = { viewModel.sendMessage(it) },
                // [수정 3] 메뉴 버튼 클릭 이벤트 전달
                onMenuClick = { scope.launch { drawerState.open() } }
            )
        }
    }
}

@Composable
fun ChatScreenContent(
    modifier: Modifier = Modifier,
    innerPadding: PaddingValues,
    messages: List<ChatMessage>,
    isLoading: Boolean,
    loadingStage: LoadingStage?,
    isSessionEnded: Boolean,
    sessionTitle: String,
    sessionGoals: List<String>,
    onSendMessage: (String) -> Unit,
    onMenuClick: () -> Unit // 메뉴 클릭 콜백 추가
) {
    val layoutDirection = LocalLayoutDirection.current
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFFF7F6FB))
            .padding(
                top = innerPadding.calculateTopPadding(),
                start = innerPadding.calculateStartPadding(layoutDirection),
                end = innerPadding.calculateEndPadding(layoutDirection)
            )
            .windowInsetsPadding(
                WindowInsets.ime.union(WindowInsets(bottom = innerPadding.calculateBottomPadding()))
            )
    ) {
        // 상단 바에 메뉴 클릭 이벤트 전달
        TopSessionBar(title = sessionTitle, onMenuClick = onMenuClick)

        MessageList(
            messages = messages,
            isLoading = isLoading,
            loadingStage = loadingStage,
            modifier = Modifier.weight(1f)
        )
        UserInput(
            isLoading = isLoading,
            isSessionEnded = isSessionEnded,
            onSendMessage = onSendMessage
        )
    }
}

// 메뉴 아이콘이 있는 상단 바
@Composable
fun TopSessionBar(
    title: String,
    onMenuClick: () -> Unit,
    onBackPressed: (() -> Unit)? = null
) {
    Surface(
        color = Color.White,
        shadowElevation = 4.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // ✅ 히스토리 화면에서만 쓸 뒤로가기 버튼
            if (onBackPressed != null) {
                IconButton(onClick = onBackPressed) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "뒤로가기",
                        tint = Color(0xFF6200EE)
                    )
                }
            }

            // 햄버거 메뉴 아이콘
            IconButton(onClick = onMenuClick) {
                Icon(
                    imageVector = Icons.Default.Menu,
                    contentDescription = "메뉴 열기",
                    tint = Color(0xFF6200EE)
                )
            }

            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = Color(0xFF6200EE),
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(start = 8.dp)
            )
        }
    }
}

@Composable
fun UserInput(
    isLoading: Boolean,
    isSessionEnded: Boolean,
    onSendMessage: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var text by remember { mutableStateOf("") }

    if (isSessionEnded) {
        Text(
            text = "상담이 종료되었습니다.",
            modifier = modifier
                .fillMaxWidth()
                .padding(16.dp),
            color = Color.Gray,
            textAlign = TextAlign.Center
        )
        return
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            modifier = Modifier.weight(1f),
            placeholder = { Text("메시지를 입력하세요...", color = Color.Gray) },
            enabled = !isLoading,
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Color(0xFFF7F6FB),
                unfocusedContainerColor = Color(0xFFF7F6FB),
                disabledContainerColor = Color(0xFFF0F0F0),
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent,
                focusedTextColor = Color.Black,
                unfocusedTextColor = Color.Black
            ),
            shape = RoundedCornerShape(12.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))

        if (isLoading) {
            CircularProgressIndicator(modifier = Modifier.size(48.dp))
        } else {
            IconButton(
                onClick = {
                    if (text.isNotBlank()) {
                        onSendMessage(text)
                        text = ""
                    }
                },
                enabled = text.isNotBlank()
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Send,
                    contentDescription = "Send Message",
                    tint = if (text.isNotBlank()) Color(0xFF6200EE) else Color.Gray
                )
            }
        }
    }
}

@Composable
fun MessageList(
    messages: List<ChatMessage>,
    isLoading: Boolean,
    loadingStage: LoadingStage?,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    // [수정] messages.size 뿐만 아니라 isLoading이 변할 때도 트리거
    LaunchedEffect(messages.size, isLoading) {
        if (messages.isNotEmpty() || isLoading) {
            coroutineScope.launch {
                // 로딩바가 생기면 아이템 개수가 1개 더 많다고 가정하고 스크롤
                val targetIndex = if (isLoading) messages.size else messages.size - 1
                if (targetIndex >= 0) {
                    listState.animateScrollToItem(targetIndex)
                }
            }
        }
    }

    LazyColumn(
        state = listState,
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp)
    ) {
        // 1. 기존 메시지 리스트
        items(messages) { msg ->
            ChatBubble(message = msg)
            Spacer(modifier = Modifier.height(8.dp))
        }

        // 2.  로딩 중일 때만 보여주는 가짜 메시지(애니메이션)
        if (isLoading) {
            item {
                GeneratingBubble(loadingStage = loadingStage)
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    when (message) {
        is ChatMessage.GuideMessage -> Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Start
        ) {
            Image(
                painter = painterResource(id = R.drawable.ic_chatbot),
                contentDescription = "Guide",
                modifier = Modifier.size(28.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Box(
                modifier = Modifier
                    .background(Color(0xFFF0F0F0), shape = RoundedCornerShape(12.dp))
                    .padding(12.dp)
                    .weight(1f, fill = false)
            ) {
                Text(text = message.text, fontSize = 16.sp, color = Color.Black)
            }
        }
        is ChatMessage.UserResponse -> Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.End
        ) {
            Box(
                modifier = Modifier
                    .background(Color(0xFFE9E0FA), shape = RoundedCornerShape(12.dp))
                    .padding(12.dp)
                    .weight(1f, fill = false)
            ) {
                Text(text = message.text, fontSize = 16.sp, color = Color.Black)
            }
        }
    }
}