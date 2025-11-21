//api.ApiService
package com.example.impulsecoachapp.api

import com.example.impulsecoachapp.data.model.chat.ChatRequest // <-- 'Next' 제거
import com.example.impulsecoachapp.data.model.chat.ChatResponse // <-- 'Next' 제거
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {

    // ... 기타 다른 API 함수들 ...

    /**
     * 새로운 단일 채팅 API (Facade)
     */
    @POST("/chat/next")
    suspend fun chatNext(@Body request: ChatRequest): ChatResponse // <-- 타입 변경

    /*
    // --- 기존 채팅 API 함수들은 주석 처리하거나 삭제 ---
    @POST("/chat/start")
    suspend fun startChat(...)

    @POST("/chat/send")
    suspend fun sendMessage(...)

    @POST("/chat/end")
    suspend fun endChat(...)
    */
}
