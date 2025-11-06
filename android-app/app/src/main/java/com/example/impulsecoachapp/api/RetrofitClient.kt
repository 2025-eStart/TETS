//retrofit

package com.example.impulsecoachapp.api

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    private const val BASE_URL = "http://192.168.68.136:8080"  // ✅ 유누님 IP 주소(서버 주소를 상수로. 개발용 로컬 IP)

    val apiService: ApiService by lazy { //by lazy: 실제로 처음 사용할 때 한 번만 생성
        Retrofit.Builder() //레트로핏 인스턴스 생성
            .baseUrl(BASE_URL) //기본 url 설정
            .addConverterFactory(GsonConverterFactory.create()) //Json 변환기
            .build()
            .create(ApiService::class.java)
    }
}



/*
// api/RetrofitClient.kt
package com.example.impulsecoachapp.api

import com.google.android.gms.tasks.Tasks
import com.google.firebase.BuildConfig
import com.google.firebase.auth.FirebaseAuth
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Route
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    // 🔧 baseUrl은 build.gradle의 BuildConfig에서 주입(빌드 타입별 전환 가능)
    private val BASE_URL: String = BuildConfig.API_BASE_URL
    private val auth: FirebaseAuth by lazy { FirebaseAuth.getInstance() }

    // 1) 매 요청에 Firebase ID 토큰을 Authorization 헤더로 붙임
    private val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val currentUser = auth.currentUser
        val token = try {
            currentUser?.let { Tasks.await(it.getIdToken(false)).token }
        } catch (_: Exception) { null }

        val req = if (token != null) {
            original.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            original
        }
        chain.proceed(req)
    }

    // 2) 401 나오면 토큰 강제 재발급 후 재시도
    private val reauthenticator = Authenticator { _: Route?, response ->
        val user = auth.currentUser ?: return@Authenticator null
        val newToken = try {
            Tasks.await(user.getIdToken(true)).token
        } catch (_: Exception) { null }

        newToken?.let {
            response.request.newBuilder()
                .header("Authorization", "Bearer $it")
                .build()
        }
    }

    // 3) 네트워크 로그(디버그 빌드에서만)
    private val logging = HttpLoggingInterceptor().apply {
        level = if (BuildConfig.DEBUG)
            HttpLoggingInterceptor.Level.BODY
        else
            HttpLoggingInterceptor.Level.NONE
    }

    // 4) OkHttp 클라이언트(타임아웃/인터셉터/재인증)
    private val okHttp: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .writeTimeout(20, TimeUnit.SECONDS)
            .addInterceptor(logging)
            .addInterceptor(authInterceptor)
            .authenticator(reauthenticator)
            .build()
    }

    // 5) Retrofit + Gson
    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(if (BASE_URL.endsWith("/")) BASE_URL else "$BASE_URL/")
            .client(okHttp)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
*/