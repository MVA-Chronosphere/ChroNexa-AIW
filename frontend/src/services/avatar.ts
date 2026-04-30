import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'

console.log('[avatar.ts] Module loaded')

export class IndianDoctorAvatar {
  private scene: THREE.Scene
  private camera: THREE.PerspectiveCamera
  private renderer: THREE.WebGLRenderer
  private avatar: THREE.Group
  private mixer: THREE.AnimationMixer | null = null
  private actions: Map<string, THREE.AnimationAction> = new Map()
  private container: HTMLElement
  private animationId: number | null = null
  private isSpeaking: boolean = false
  private audioContext: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private dataArray: Uint8Array | null = null

  constructor(container: HTMLElement) {
    console.log('[IndianDoctorAvatar] Constructor called')
    this.container = container

    // Ensure container has dimensions
    const width = Math.max(container.clientWidth || 400, 100)
    const height = Math.max(container.clientHeight || 600, 100)
    console.log('[IndianDoctorAvatar] Container dimensions:', width, 'x', height)

    // Scene setup
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0xffffff)
    console.log('[IndianDoctorAvatar] Scene created')

    // Camera setup
    this.camera = new THREE.PerspectiveCamera(
      50,
      width / height,
      0.1,
      200
    )
    // Will be repositioned after model loads
    this.camera.position.set(0, 1.4, 0.6)
    this.camera.lookAt(0, 1.3, 0)
    console.log('[IndianDoctorAvatar] Camera positioned for chest-level portrait view')

    // Renderer setup
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    this.renderer.setSize(width, height)
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap
    this.renderer.outputColorSpace = THREE.SRGBColorSpace
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping
    this.renderer.toneMappingExposure = 1.2
    console.log('[IndianDoctorAvatar] Renderer created')
    
    // Clear container and append renderer
    container.innerHTML = ''
    this.renderer.domElement.style.display = 'block'
    this.renderer.domElement.style.width = '100%'
    this.renderer.domElement.style.height = '100%'
    container.appendChild(this.renderer.domElement)
    console.log('[IndianDoctorAvatar] Canvas appended, size:', this.renderer.domElement.width, this.renderer.domElement.height)

    // Lighting
    this.setupLighting()

    // Avatar group (will hold the model)
    this.avatar = new THREE.Group()
    this.scene.add(this.avatar)

    // Load 3D model
    this.loadAvatarModel()
    console.log('[IndianDoctorAvatar] Loading avatar model...')

    // Start animation loop
    this.animate()
    console.log('[IndianDoctorAvatar] Animation loop started')

    // Handle window resize
    window.addEventListener('resize', () => this.onWindowResize())
    console.log('[IndianDoctorAvatar] Constructor complete')
  }

  private setupLighting() {
    console.log('[IndianDoctorAvatar] Setting up lighting')
    // Ambient light - bright and even
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5)
    this.scene.add(ambientLight)

    // Directional light (sun)
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2)
    directionalLight.position.set(3, 8, 5)
    directionalLight.castShadow = true
    directionalLight.shadow.mapSize.width = 2048
    directionalLight.shadow.mapSize.height = 2048
    this.scene.add(directionalLight)

    // Point light for fill - front facing
    const pointLight = new THREE.PointLight(0xffffff, 1.0)
    pointLight.position.set(-3, 3, 8)
    this.scene.add(pointLight)
    
    // Front fill light - increased for face visibility
    const frontLight = new THREE.PointLight(0xffffff, 1.2)
    frontLight.position.set(0, 2, 10)
    this.scene.add(frontLight)
  }

  private loadAvatarModel() {
    const loader = new GLTFLoader()
    let modelLoaded = false
    
    // Load Indian female doctor avatar
    const modelUrl = '/indian_doctor.glb'

    console.log(`[IndianDoctorAvatar] Attempting to load model from: ${modelUrl}`)
    
    loader.load(
      modelUrl,
      (gltf) => {
        console.log('[IndianDoctorAvatar] ✓ Model loaded successfully!')
        modelLoaded = true
        
        const model = gltf.scene
        
        // Disable frustum culling on all meshes (critical for skinned meshes)
        model.traverse((node) => {
          if ((node as THREE.Mesh).isMesh) {
            ;(node as THREE.Mesh).frustumCulled = false
          }
        })

        // Reset transforms
        model.position.set(0, 0, 0)
        model.rotation.set(0, 0, 0)
        model.scale.set(1, 1, 1)
        
        // Add model directly to scene (not through group — fixes skinned mesh visibility)
        this.scene.add(model)
        
        // Calculate bounding box AFTER adding to scene
        const box = new THREE.Box3().setFromObject(model)
        const size = box.getSize(new THREE.Vector3())
        const center = box.getCenter(new THREE.Vector3())
        
        console.log('[IndianDoctorAvatar] Model size:', { x: size.x, y: size.y, z: size.z })
        console.log('[IndianDoctorAvatar] Model center:', { x: center.x, y: center.y, z: center.z })
        console.log('[IndianDoctorAvatar] Model bounds:', { minY: box.min.y, maxY: box.max.y })
        
        // Camera: chest-to-head framing
        const lookAtY = box.min.y + size.y * 0.75
        const cameraDistance = size.y * 0.45
        
        this.camera.position.set(center.x, lookAtY, center.z + cameraDistance)
        this.camera.lookAt(center.x, lookAtY, center.z)
        this.camera.updateProjectionMatrix()
        
        // Store model ref for speaking animation
        this.avatar = model as unknown as THREE.Group
        
        console.log('[IndianDoctorAvatar] Camera:', { lookAtY: lookAtY.toFixed(3), cameraDistance: cameraDistance.toFixed(3) })
        console.log('[IndianDoctorAvatar] Model added to scene')
        
        // Setup animation mixer if the model has animations
        if (gltf.animations.length > 0) {
          this.mixer = new THREE.AnimationMixer(model)
          gltf.animations.forEach((clip) => {
            const action = this.mixer!.clipAction(clip)
            this.actions.set(clip.name, action)
          })
          console.log(`[IndianDoctorAvatar] ✓ Loaded ${gltf.animations.length} animations`)
          console.log('[IndianDoctorAvatar] Available animations:', gltf.animations.map(a => a.name).join(', '))
          
          // Auto-play idle/rest animation if available, otherwise play first one
          let idleAction: THREE.AnimationAction | null = null
          for (const clip of gltf.animations) {
            if (clip.name.toLowerCase().includes('idle') || 
                clip.name.toLowerCase().includes('rest') ||
                clip.name.toLowerCase().includes('stand') ||
                clip.name.toLowerCase().includes('default')) {
              idleAction = this.mixer!.clipAction(clip)
              console.log(`[IndianDoctorAvatar] Auto-playing animation: ${clip.name}`)
              break
            }
          }
          
          // If no idle animation found, play the first one
          if (!idleAction && gltf.animations.length > 0) {
            idleAction = this.mixer!.clipAction(gltf.animations[0])
            console.log(`[IndianDoctorAvatar] No idle animation found, playing first: ${gltf.animations[0].name}`)
          }
          
          if (idleAction) {
            idleAction.play()
          }
        }
      },
      (progress) => {
        const percent = Math.round((progress.loaded / progress.total) * 100)
        if (percent % 25 === 0) { // Log at 0%, 25%, 50%, 75%, 100%
          console.log(`[IndianDoctorAvatar] Loading: ${percent}%`)
        }
      },
      (error) => {
        console.error('[IndianDoctorAvatar] ✗ Failed to load model:', error.message)
        console.error('[IndianDoctorAvatar] Error details:', error)
        if (!modelLoaded) {
          console.log('[IndianDoctorAvatar] Model loading failed - creating simple fallback')
          this.createFallbackAvatar()
        }
      }
    )
  }

  private createFallbackAvatar() {
    console.log('[IndianDoctorAvatar] Creating simple fallback avatar')
    
    const skinMaterial = new THREE.MeshStandardMaterial({
      color: 0xd4a574,
      roughness: 0.7,
      metalness: 0
    })

    // Head
    const headGeometry = new THREE.SphereGeometry(0.3, 32, 32)
    const head = new THREE.Mesh(headGeometry, skinMaterial)
    head.position.y = 0.5
    head.castShadow = true
    this.avatar.add(head)

    // Body (white coat)
    const bodyGeometry = new THREE.BoxGeometry(0.5, 0.8, 0.3)
    const coatMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.6
    })
    const body = new THREE.Mesh(bodyGeometry, coatMaterial)
    body.position.y = -0.1
    body.castShadow = true
    this.avatar.add(body)

    console.log('[IndianDoctorAvatar] Simple fallback avatar created')
  }

  public setEmotion(emotion: 'neutral' | 'happy' | 'sad' | 'surprised') {
    console.log(`[IndianDoctorAvatar] Avatar emotion set to: ${emotion}`)
  }

  public animate = () => {
    this.animationId = requestAnimationFrame(this.animate)
    
    // Update mixer if it exists
    if (this.mixer) {
      this.mixer.update(0.016) // 60fps
    }
    
    this.renderer.render(this.scene, this.camera)
  }

  private onWindowResize() {
    const width = Math.max(this.container.clientWidth || 400, 100)
    const height = Math.max(this.container.clientHeight || 600, 100)

    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(width, height)
  }

  public speak(duration: number, audioElement?: HTMLAudioElement) {
    console.log(`[IndianDoctorAvatar] Avatar speaking for ${duration}ms`)
    this.isSpeaking = true
    
    // Setup audio analysis for reactive animation
    if (audioElement && !this.audioContext) {
      try {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
        this.analyser = this.audioContext.createAnalyser()
        this.analyser.fftSize = 256
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount)
        
        // Connect audio element to analyser
        const source = this.audioContext.createMediaElementAudioSource(audioElement)
        source.connect(this.analyser)
        this.analyser.connect(this.audioContext.destination)
        console.log('[IndianDoctorAvatar] Audio analysis setup complete')
      } catch (e) {
        console.warn('[IndianDoctorAvatar] Audio context setup failed:', e)
      }
    }
    
    const startTime = Date.now()
    const originalY = this.avatar.position.y
    const originalScaleY = this.avatar.scale.y
    
    const animateSpeaking = () => {
      const elapsed = Date.now() - startTime
      
      if (elapsed < duration && this.isSpeaking) {
        let audioEnergy = 0
        
        // Get audio frequency data if available
        if (this.analyser && this.dataArray) {
          this.analyser.getByteFrequencyData(this.dataArray)
          // Calculate average frequency energy
          for (let i = 0; i < this.dataArray.length; i++) {
            audioEnergy += this.dataArray[i]
          }
          audioEnergy = audioEnergy / this.dataArray.length / 255 // Normalize to 0-1
        }
        
        // Animated head bob and body scale
        const time = elapsed / 200
        const phase = Math.sin(time * Math.PI * 2) // Oscillating movement
        
        // Head bob
        this.avatar.position.y = originalY + Math.sin(phase) * 0.08 + audioEnergy * 0.1
        
        // Body scale animation (simulate jaw/mouth movement by scaling)
        const scaleVariation = 1 + audioEnergy * 0.05 + Math.abs(Math.sin(phase * 3)) * 0.02
        this.avatar.scale.y = originalScaleY * scaleVariation
        
        // Slight rotation for added expression
        this.avatar.rotation.z = Math.sin(time) * 0.02
        
        requestAnimationFrame(animateSpeaking)
      } else {
        // Reset to original state
        this.avatar.position.y = originalY
        this.avatar.scale.y = originalScaleY
        this.avatar.rotation.z = 0
        this.isSpeaking = false
      }
    }
    
    animateSpeaking()
  }

  public dispose() {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId)
    }
    window.removeEventListener('resize', () => this.onWindowResize())
    this.renderer.dispose()
  }
}
