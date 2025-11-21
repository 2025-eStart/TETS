// di.AppModule
//Dummy 대신 Actual을 사용하도록 스위칭하고, 서버 주소를 langgraph server에 맞게 올바르게 설정
package com.example.impulsecoachapp.di

import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.domain.repository.ChatRepository
import com.google.firebase.auth.FirebaseAuth
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class AppModule {

    // ★ 중요: 이제 실제 서버와 통신하므로 ActualChatRepository를 바인딩합니다.
    @Binds
    @Singleton
    abstract fun bindChatRepository(
        actualChatRepository: ActualChatRepository
    ): ChatRepository

    companion object {
        @Provides
        @Singleton
        fun provideFirebaseAuth(): FirebaseAuth {
            return FirebaseAuth.getInstance()
        }
    }
}