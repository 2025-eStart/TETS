//api.ApiService
package com.example.impulsecoachapp.api

import com.example.impulsecoachapp.data.model.chat.LangGraphRequest
import com.example.impulsecoachapp.data.model.chat.LangGraphResponse
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {

    /**
     * LangGraph 실행 및 대기 (Synchronous)
     * POST /threads/{thread_id}/runs/wait
     * * @param threadId: 사용자 ID (또는 세션 ID)를 스레드 ID로 사용
     */
    @POST("threads/{threadId}/runs/wait")
    suspend fun sendMessage(
        @Path("threadId") threadId: String,
        @Body request: LangGraphRequest
    ): LangGraphResponse
}