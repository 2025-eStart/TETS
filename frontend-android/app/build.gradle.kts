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
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
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

    //Testing
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}