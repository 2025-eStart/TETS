package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

////////////////// API 연동 없는 버전 //////////////////
@Singleton
class DummyChatRepository @Inject constructor() : ChatRepository {

    // 1. 대화 시나리오의 "단계"를 기억할 상태 변수
    private var conversationStep = 0

    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {

        // API 호출을 흉내 내기 위한 1초 딜레이
        delay(1000)

        // 2. 사용자가 "종료"를 누르면, 시나리오와 관계없이 즉시 종료
        if (endSession) {
            conversationStep = 0 // (데모를 위해) 세션 리셋
            val endMessage = ChatMessage.GuideMessage("알겠어, 오늘 상담은 여기까지 하자! 수고했어.")
            val chatTurn = ChatTurn(
                assistantMessage = endMessage,
                isSessionEnded = true,
                homework = null
            )
            return Result.success(chatTurn)
        }

        // 3. (핵심) 사용자가 무엇을 입력하든(text), 정해진 시나리오대로 응답
        val replyMessage: ChatMessage
        var isEnded = false

        when (conversationStep) {
            // ViewModel의 init 메시지("...오늘 어떤 일이 있었니?")에 대한 첫 번째 응답
            // user: "충동적으로 신발을 샀는데, '이거 지금 안 사면 놓쳐'라는 생각이 들었어"
            0 -> {
                replyMessage = ChatMessage.GuideMessage("그 생각이 들었을 때, 몸이나 감정은 어땠나요? 예를 들어 조급하거나 불안하거나, 혹은 흥분된 느낌이 있었을 수도 있어요.")
            }
            // user: "맞아 그랬던 것 같아"
            1 -> {
                replyMessage = ChatMessage.GuideMessage("좋아요. ‘금방 품절될 것 같다’는 생각 속에는 어떤 믿음이 숨어 있을까요?\n혹시 ‘기회를 놓치면 후회할 거야’ 같은 생각이 함께 있었나요?")
            }
            // user: "응 나중에 못 사면 후회할 것 같았어"
            2 -> {
                replyMessage = ChatMessage.GuideMessage("이전에도 비슷한 생각을 한 적이 있었나요?\n‘지금 안 사면 후회할 거야’라고 느꼈던 적이 있었을 때, 정말 후회가 오래갔나요?")
            }
            // user: "상담을 종료합니다"
            3 -> {
                replyMessage = ChatMessage.GuideMessage("오늘 상담 감사합니다.\n[요약]: '놓칠 수 있다'는 자동적 사고를 인지하셨어요. 다음 주까지 수행해야 할 과제는 이 사고를 객관적인 증거로 반박하는 '사고 반박하기'입니다. ")
                isEnded = true // 챗봇이 대화를 종료시킴
            }
            // 3단계 이후의 모든 메시지 (세션이 이미 종료됨)
            else -> {
                replyMessage = ChatMessage.GuideMessage("오늘 상담은 종료되었어. 내일 또 얘기하자!")
                isEnded = true
            }
        }

        // 4. 다음 메시지를 위해 단계를 1 증가시킴
        if (isEnded) {
            // 세션이 종료되면, 다음 데모를 위해 단계를 리셋
            conversationStep = 0
        } else {
            conversationStep++
        }

        val chatTurn = ChatTurn(
            assistantMessage = replyMessage,
            isSessionEnded = isEnded,
            homework = null
        )

        return Result.success(chatTurn)
    }
}
