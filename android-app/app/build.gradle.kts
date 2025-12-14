plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.kapt) // Kapt 플러그인 적용
    alias(libs.plugins.hilt)        // Hilt 플러그인 적용
}

android {
    namespace = "com.example.impulsecoachapp"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.impulsecoachappv2"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
    }

    buildTypes {
        debug{
            // 디버그: 내부 IP(HTTP) — 개발 편의용
            // buildConfigField("String", "API_BASE_URL", "\"http://192.168.68.136:8080/\"")

            // LangGraph 기본 포트는 8123, 또는 2024
            // 에뮬레이터 사용 시: "http://10.0.2.2:8123/"
            // 실기기 사용 시: "http://내_PC_IP주소:8123/"
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8123/\"")
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // 릴리즈: 반드시 HTTPS 운영 도메인 (실제 도메인)
            buildConfigField("String", "API_BASE_URL", "\"https://api.yourdomain.com/\"")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlin {
        jvmToolchain(17)
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    packaging.resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"

}

dependencies {
    // Compose BOM을 추가
    val composeBom = platform(libs.androidx.compose.bom)
    implementation(composeBom)
    androidTestImplementation(composeBom) // 테스트에서도 BOM 적용

    //App & UI
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    //implementation(libs.androidx.material)
    implementation(libs.androidx.material3)

    //architecture
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)

    //Firebase
    implementation(libs.firebase.auth)
    implementation(platform(libs.firebase.bom))

    // Hilt Core
    implementation(libs.hilt.android)
    kapt(libs.hilt.compiler)

    // Hilt + ViewModel (Compose UI 사용 시)
    implementation(libs.hilt.navigation.compose)

    //Retrofit
    implementation(libs.square.retrofit)
    implementation(libs.square.converter.gson)
    implementation(libs.kotlinx.coroutines.android)

    //OkHttp logging
    implementation(libs.logging.interceptor)

    //Testing
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}
kapt {
    correctErrorTypes = true
}