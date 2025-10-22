package com.example.impulsecoachapp.di

import com.example.impulsecoachapp.api.ApiService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    // Hilt가 Retrofit을 만들 수 있도록 @Provides 추가
    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit {
        return Retrofit.Builder()
            .baseUrl("http://127.0.0.1:8000") // [중요] 실제 서버 주소로 변경하세요!
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    // Hilt가 ApiService를 만들 수 있도록 @Provides 추가
    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService {
        return retrofit.create(ApiService::class.java)
    }
}
