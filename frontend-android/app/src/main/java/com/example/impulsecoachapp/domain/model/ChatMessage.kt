package com.example.impulsecoachapp.domain.model

sealed class ChatMessage {
    // 1. [수정] 이 클래스를 상속받는 모든 자식은
    //    'text'라는 String 속성을 "반드시" 가져야 한다고 'abstract'로 선언합니다.
    //    (타입을 Any에서 String으로 변경)
    abstract val text: String

    // 2. [수정] 부모의 'abstract val text'를 구현(override)한다고 명시합니다.
    data class GuideMessage(override val text: String) : ChatMessage()

    // 3. [수정] 부모의 'abstract val text'를 구현(override)한다고 명시합니다.
    data class UserResponse(override val text: String) : ChatMessage()
}
