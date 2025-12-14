// di.AppModule
package com.example.impulsecoachapp.di

import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.domain.repository.ChatRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class AppModule {

    @Binds
    @Singleton
    abstract fun bindChatRepository(
        actualChatRepository: ActualChatRepository
    ): ChatRepository

    // [삭제] FirebaseAuth provide 함수 삭제함 (로그인 기능 삭제)
    /*
    companion object {
        @Provides
        @Singleton
        fun provideFirebaseAuth(): FirebaseAuth { ... }
    }
    */
}
