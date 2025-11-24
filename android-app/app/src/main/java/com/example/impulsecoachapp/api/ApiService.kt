//api.ApiService
package com.example.impulsecoachapp.api

import com.example.impulsecoachapp.data.model.chat.*
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {

    // 1. 세션 초기화 (채팅방 배정 요청)
    @POST("session/init")
    suspend fun initSession(@Body request: InitSessionRequest): InitSessionResponse

    // 2. 대화하기 (메시지 전송)
    @POST("chat")
    suspend fun sendChatMessage(@Body request: ChatRequest): ChatResponse
}