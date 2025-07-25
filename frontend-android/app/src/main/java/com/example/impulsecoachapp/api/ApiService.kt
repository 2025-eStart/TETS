//retrofit
package com.example.impulsecoachapp.api

import com.example.impulsecoachapp.data.Transaction
import com.example.impulsecoachapp.data.model.chat.ChatRequest
import com.example.impulsecoachapp.data.model.chat.ChatResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("/chat")
    suspend fun sendChat(@Body request: ChatRequest): Response<ChatResponse>

    @POST("transactions")
    suspend fun postTransaction(@Body transaction: Transaction): Response<Unit>

}

