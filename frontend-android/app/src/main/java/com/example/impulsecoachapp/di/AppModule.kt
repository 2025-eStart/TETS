package com.example.impulsecoachapp.di

import com.example.impulsecoachapp.domain.repository.ChatRepository
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.data.repository.DummyChatRepository
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
    // "ChatRepository(인터페이스)를 요청하면 DummyChatRepository(구현체)를 줘라"
    @Binds
    @Singleton
    abstract fun bindChatRepository(
        dummyChatRepository: DummyChatRepository // [수정] Actual -> Dummy
    ): ChatRepository
    /*
    // 서버가 준비되면 이 코드로 다시 바꿀 것
    // 서버가 준비되면, 이 부분 주석처리를 해제하고 위 블럭을 주석처리하면 됨.
     // "ChatRepository(인터페이스)를 요청하면 ActualChatRepository(구현체)를 줘라"
    @Binds
    @Singleton
    abstract fun bindChatRepository(
        actualChatRepository: ActualChatRepository
    ): ChatRepository
    */

    // Hilt가 FirebaseAuth를 만들 수 있도록 @Provides 추가
    companion object {
        @Provides
        @Singleton
        fun provideFirebaseAuth(): FirebaseAuth {
            return FirebaseAuth.getInstance()
        }
    }
}
