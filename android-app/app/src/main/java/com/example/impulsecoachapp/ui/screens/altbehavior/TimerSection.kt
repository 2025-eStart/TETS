package com.example.impulsecoachapp.ui.screens.altbehavior


import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.impulsecoachapp.ui.sound.AltBehaviorSoundPlayer
import kotlinx.coroutines.delay
import java.util.Locale

enum class BreathingPhase(val label: String) {
    Inhale("들이마시세요"),
    Hold("참으세요"),
    Exhale("내쉬세요")
}

@Composable
fun TimerSection(
    onFinish: () -> Unit,
    onInterrupt: () -> Unit = {}
) {
    val viewModel: TimerViewModel = viewModel()
    val configuration = LocalConfiguration.current
    val density = LocalDensity.current

    val screenHeight = configuration.screenHeightDp.dp
    val screenHeightPx = with(density) { screenHeight.toPx() }

    val waveOffset = remember { Animatable(0f) }
    val phase by viewModel.phase.collectAsState()
    var timeLeft by remember { mutableIntStateOf(180) }
    var running by remember { mutableStateOf(true) }

    // ✅ BGM via TimerSoundPlayer
    val context = LocalContext.current
    val soundPlayer = remember { AltBehaviorSoundPlayer(context) }

    LaunchedEffect(Unit) {
        soundPlayer.play()
    }

    DisposableEffect(Unit) {
        onDispose {
            soundPlayer.release()
            viewModel.releaseSound()
        }
    }

    // ✅ phase에 따라 wave 위치 조절
    LaunchedEffect(phase) {
        when (phase) {
            BreathingPhase.Inhale -> {
                waveOffset.animateTo(
                    targetValue = 0f,
                    animationSpec = tween(4000, easing = FastOutSlowInEasing)
                )
            }
            BreathingPhase.Exhale -> {
                waveOffset.animateTo(
                    targetValue = screenHeightPx,
                    animationSpec = tween(4000, easing = FastOutSlowInEasing)
                )
            }
            BreathingPhase.Hold -> {
                delay(2000L)
            }
        }
    }

    // ✅ breathing loop
    LaunchedEffect(Unit) {
        while (running && timeLeft > 0) {
            viewModel.setPhase(BreathingPhase.Inhale)
            viewModel.playPhaseSound()
            delay(4000L)

            viewModel.setPhase(BreathingPhase.Hold)
            viewModel.playPhaseSound()
            delay(2000L)

            viewModel.setPhase(BreathingPhase.Exhale)
            viewModel.playPhaseSound()
            delay(4000L)

            viewModel.setPhase(BreathingPhase.Hold)
            viewModel.playPhaseSound()
            delay(2000L)
        }
        if (running) onFinish()
    }

    // ✅ timer 감소
    LaunchedEffect(Unit) {
        while (running && timeLeft > 0) {
            delay(1000L)
            timeLeft--
        }
    }

    // ✅ 화면 UI
    Box(
        modifier = Modifier
            .fillMaxSize()
            .clickable {
                if (running) {
                    running = false
                    onInterrupt()
                }
            }
            .background(Color.Black),
        contentAlignment = Alignment.Center
    ) {
        // ✅ wave (Canvas 기반 곡선 wave)
        Canvas(modifier = Modifier.fillMaxSize()) {
            val waveHeight = size.height * 0.1f
            val waveTop = waveOffset.value

            val path = Path().apply {
                moveTo(0f, waveTop)
                quadraticTo(size.width / 2, waveTop - waveHeight, size.width, waveTop)
                lineTo(size.width, size.height)
                lineTo(0f, size.height)
                close()
            }

            drawPath(
                path = path,
                brush = Brush.verticalGradient(
                    colors = listOf(Color(0xFF0B1D3A), Color(0xFF1E2F50))
                )
            )
        }

        // ✅ 텍스트 정보
        Column(
            modifier = Modifier.align(Alignment.Center),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = phase.label, fontSize = 20.sp, color = Color.White)
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = String.format(Locale.getDefault(), "%02d:%02d", timeLeft / 60, timeLeft % 60),
                fontSize = 36.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
        }
    }
}
