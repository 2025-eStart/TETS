//api.ApiService
package com.example.impulsecoachapp.api

import com.example.impulsecoachapp.data.model.chat.*
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.GET
import retrofit2.http.Path

interface ApiService {

    // 1. 세션 초기화 (채팅방 배정 요청)
    @POST("session/init")
    suspend fun initSession(@Body request: InitSessionRequest): InitSessionResponse

    // 2. 대화하기 (메시지 전송)
    @POST("chat")
    suspend fun sendChatMessage(@Body request: ChatRequest): ChatResponse

    // 3. 과거 세션 목록 조회
    @GET("sessions/{userId}")
    suspend fun getSessions(@Path("userId") userId: String): List<SessionSummary>

    // 과거 대화 상세 내역 가져오기
    @GET("history/{userId}/{threadId}")
    suspend fun getSessionHistory(
        @Path("userId") userId: String,
        @Path("threadId") threadId: String
    ): List<MessageHistoryResponse>
}