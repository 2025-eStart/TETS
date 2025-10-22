package com.example.impulsecoachapp.ui.screens.chat

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.impulsecoachapp.R
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold
import com.example.impulsecoachapp.ui.theme.ImpulseCoachAppTheme // [추가] 2번 오류 해결
import kotlinx.coroutines.launch

/**
 * 1. "Smart" Composable (Route)
 * - ViewModel을 주입받고, 상태를 수집하여 "Dumb" Composable에 전달합니다.
 */
@Composable
fun ChatScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    onBackPressed: () -> Unit,
    viewModel: ChatViewModel = hiltViewModel() // Hilt로 ViewModel 주입
) {
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val isSessionEnded by viewModel.isSessionEnded.collectAsState()

    ScreenScaffold(
        selectedTab = selectedTab,
        onTabSelected = onTabSelected
    ) { innerPadding ->
        // 2. 상태와 람다를 "Dumb" Composable인 ChatScreenContent에 전달
        ChatScreenContent(
            modifier = Modifier.padding(innerPadding),
            messages = messages,
            isLoading = isLoading,
            isSessionEnded = isSessionEnded,
            onSendMessage = { text ->
                viewModel.sendMessage(text)
            }
        )
    }
}

/**
 * 3. "Dumb" Composable (Content)
 * - ViewModel을 모르며, 오직 받은 데이터로 UI만 그립니다.
 * - 이 함수는 Preview가 매우 쉽습니다.
 */
@Composable
fun ChatScreenContent(
    modifier: Modifier = Modifier,
    messages: List<ChatMessage>,
    isLoading: Boolean,
    isSessionEnded: Boolean,
    onSendMessage: (String) -> Unit
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFFF7F6FB))
    ) {
        TopDateTimeBar()
        MessageList(
            messages = messages,
            modifier = Modifier.weight(1f)
        )
        UserInput(
            isLoading = isLoading,
            isSessionEnded = isSessionEnded,
            onSendMessage = onSendMessage
        )
    }
}


// [수정 없음] UserInput (이전과 동일)
@Composable
fun UserInput(
    isLoading: Boolean,
    isSessionEnded: Boolean,
    onSendMessage: (String) -> Unit
) {
    var text by remember { mutableStateOf("") }

    if (isSessionEnded) {
        Text(
            text = "상담이 종료되었습니다.",
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            color = Color.Gray,
            textAlign = TextAlign.Center
        )
        return
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            modifier = Modifier.weight(1f),
            placeholder = { Text("메시지를 입력하세요...") },
            enabled = !isLoading,
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Color(0xFFF7F6FB),
                unfocusedContainerColor = Color(0xFFF7F6FB),
                disabledContainerColor = Color(0xFFF0F0F0),
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent,
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
                    imageVector = Icons.Default.Send,
                    contentDescription = "Send Message",
                    tint = if (text.isNotBlank()) Color(0xFF6200EE) else Color.Gray
                )
            }
        }
    }
}

// [수정 없음] TopDateTimeBar (이전과 동일)
@Composable
fun TopDateTimeBar() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("2025.07.01.화요일", fontSize = 14.sp, color = Color.Gray)
        Text("14:03", fontSize = 14.sp, color = Color.Gray)
        Image(
            painter = painterResource(id = R.drawable.ic_user_profile),
            contentDescription = "User",
            modifier = Modifier.size(32.dp)
        )
    }
}

// [수정 없음] MessageList (이전과 동일, 1번 오류 해결을 위해 import만 추가)
@Composable
fun MessageList(
    messages: List<ChatMessage>,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope() // [추가] 1번 오류 해결

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            coroutineScope.launch {
                listState.animateScrollToItem(messages.size - 1)
            }
        }
    }

    LazyColumn(
        state = listState,
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp)
    ) {
        items(messages) { msg ->
            ChatBubble(message = msg)
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

// [수정 없음] ChatBubble (이전과 동일)
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
                Text(text = message.text, fontSize = 16.sp)
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
                Text(text = message.text, fontSize = 16.sp)
            }
        }
    }
}

/**
 * 4. [수정] Preview가 "Dumb" Composable인 ChatScreenContent를 호출
 * - HiltViewModel()과 관련이 없어지므로 3번 오류가 해결됩니다.
 */
@Preview(showSystemUi = true, showBackground = true)
@Composable
fun PreviewChatScreen() {
    ImpulseCoachAppTheme { // 2번 오류 해결
        // 가짜 데이터 생성
        val fakeMessages = listOf(
            ChatMessage.GuideMessage("안녕! 나는 너의 소비 습관을 함께 돌아볼 임펄스 코치야. 오늘 어떤 일이 있었니?"),
            ChatMessage.UserResponse("네 있었어요"),
            ChatMessage.GuideMessage("무슨 소비였는지 말해줄 수 있어?"),
            ChatMessage.UserResponse("밤에 쇼핑앱을 너무 오래 봤어요."),
            ChatMessage.GuideMessage("그렇구나, 쇼핑앱을 볼 때 기분이 어땠어?"),
            ChatMessage.UserResponse("그냥... 스트레스가 풀리는 것 같았어요."),
            ChatMessage.GuideMessage("스트레스가 풀리는 느낌이었구나.")
        )

        ChatScreenContent(
            messages = fakeMessages,
            isLoading = false,
            isSessionEnded = false,
            onSendMessage = {} // Preview에서는 아무것도 안 함
        )
    }
}
