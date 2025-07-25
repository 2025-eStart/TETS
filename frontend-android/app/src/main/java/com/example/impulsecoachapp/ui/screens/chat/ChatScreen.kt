package com.example.impulsecoachapp.ui.screens.chat

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.impulsecoachapp.R
import com.example.impulsecoachapp.data.model.chat.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold

@Composable
fun ChatScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    onBackPressed: () -> Unit,
    viewModel: ChatViewModel = viewModel()
) {
    val messages by viewModel.messages.collectAsState()

    ScreenScaffold(
        selectedTab = selectedTab,
        onTabSelected = onTabSelected
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .background(Color(0xFFF7F6FB))
        ) {
            TopDateTimeBar()
            MessageList(
                messages = messages,
                onOptionSelected = { viewModel.handleUserSelection(it) },
                modifier = Modifier.weight(1f) // [수정] 메시지 리스트가 남은 공간을 모두 차지하도록
            )
            // [추가] 사용자 입력 컴포저블
            UserInput(
                onSendMessage = { text ->
                    viewModel.sendMessage(text)
                }
            )
        }
    }
}

// [추가] 사용자 입력을 위한 컴포저블
@Composable
fun UserInput(onSendMessage: (String) -> Unit) {
    var text by remember { mutableStateOf("") }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            modifier = Modifier.weight(1f),
            placeholder = { Text("메시지를 입력하세요...") }
        )
        Spacer(modifier = Modifier.width(8.dp))
        IconButton(onClick = {
            if (text.isNotBlank()) {
                onSendMessage(text)
                text = "" // 메시지 전송 후 입력창 비우기
            }
        }) {
            Icon(
                imageVector = Icons.Default.Send,
                contentDescription = "Send Message",
                tint = Color.Gray
            )
        }
    }
}


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

@Composable
fun MessageList(
    messages: List<ChatMessage>,
    onOptionSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp),
        reverseLayout = true
    ) {
        items(messages.reversed()) { msg ->
            ChatBubble(message = msg, onOptionSelected = onOptionSelected)
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage, onOptionSelected: (String) -> Unit) {
    when (message) {
        is ChatMessage.GuideMessage -> Row {
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
            ) {
                Text(text = message.text, fontSize = 16.sp)
            }
        }
        is ChatMessage.ChoiceMessage -> {
            // [수정] 선택지 버튼 UI는 그대로 두거나, 텍스트 입력과 병행할 수 있도록 유지합니다.
            // 여기서는 사용자가 텍스트로 자유롭게 입력하는 것이 주된 시나리오이므로,
            // 이 UI가 나타나는 빈도는 줄어들 수 있습니다.
            Column {
                message.options.forEach { option ->
                    Button(
                        onClick = { onOptionSelected(option) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                    ) {
                        Text(option)
                    }
                }
            }
        }
    }
}

@Preview(showSystemUi = true, showBackground = true)
@Composable
fun PreviewChatScreen() {
    ChatScreen(
        selectedTab = BottomTab.Chat,
        onTabSelected = {},
        onBackPressed = {}
    )
}