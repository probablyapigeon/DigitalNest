// LUMINA Core v0.5 — executable XC program used by LUMINA v0.3.2 Coupled Environment.
// State names are operational visualization/control channels, not physical or psychological measurements.
// v0.3 adds bounded structural morphogenesis using XC Runtime v0.3.1.2.
// v0.4 added DialogueInput. v0.5 adds EnvironmentFeedback for the declared sensor boundary.
// The bridge encoder is DERIVED_TEXT_ENCODING; XC does not claim that it measures literal semantics or emotion.
// Morphogenesis is classical persistent software-structure growth, not biological morphogenesis.

xembra LuminaCore version 0.5 {
  seed = 260914

  state Psi {
    entropy: real = 0.28
    cohesion: real = 0.62
    resonance: real = 0.48
    oscillation: real = 0.36
    branch_pressure: real = 0.30
    memory_salience: real = 0.18
    distortion: real = 0.16
    brightness: real = 0.70
  }

  memory FieldMemory {
    capacity = 96
    decay = 0.08
    top_k = 6
    similarity_weight = 0.35
    salience_weight = 0.40
    recency_weight = 0.25
  }

  observation MusicPulse {
    vector = [ 0.12, 0.02, 0.18, 0.22, 0.10, 0.08, 0.04, 0.10 ]
    kind = "audio"
    salience = 0.70
  }

  observation HarmonicRise {
    vector = [ -0.03, 0.10, 0.24, 0.08, 0.02, 0.10, -0.04, 0.14 ]
    kind = "audio"
    salience = 0.78
  }

  observation NovelInput {
    vector = [ 0.20, -0.06, 0.05, 0.10, 0.24, 0.14, 0.18, 0.05 ]
    kind = "semantic"
    salience = 0.88
  }

  observation Quiet {
    vector = [ -0.10, 0.12, -0.08, -0.12, -0.10, 0.02, -0.08, -0.04 ]
    kind = "rest"
    salience = 0.25
  }

  // Dynamic dialogue ingress. The declared zero vector is a safe baseline.
  // During /api/dialogue the bridge supplies a deterministic 8D override and
  // records the exact vector + provenance in the causal trace.
  observation DialogueInput {
    vector = [ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00 ]
    kind = "dialogue"
    salience = 0.50
  }

  // Dynamic sensor ingress from the coupled simulated environment. The bridge
  // supplies an explicit 8D override produced by ObservationEncoder O(r).
  // Raw environment state E is never exposed to XC through this declaration.
  observation EnvironmentFeedback {
    vector = [ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00 ]
    kind = "sim_environment_sensor"
    salience = 0.40
  }

  matrix F = [
    [ 1.03, -0.08,  0.04,  0.02,  0.05,  0.00,  0.06,  0.01],
    [-0.02,  1.04,  0.05, -0.02, -0.04,  0.04, -0.03,  0.02],
    [ 0.03,  0.02,  1.05,  0.06,  0.01,  0.03,  0.04,  0.00],
    [ 0.01, -0.03,  0.07,  1.02,  0.05,  0.00,  0.03,  0.02],
    [ 0.06, -0.02,  0.01,  0.04,  1.03,  0.03,  0.08,  0.00],
    [ 0.00,  0.03,  0.02,  0.00,  0.04,  1.04,  0.01,  0.03],
    [ 0.05, -0.01,  0.03,  0.02,  0.09,  0.01,  1.02,  0.02],
    [ 0.01,  0.02,  0.02,  0.03,  0.00,  0.03,  0.01,  1.03]
  ]

  matrix V = [
    [ 1.01, -0.02,  0.08,  0.04,  0.10,  0.01,  0.03,  0.00],
    [ 0.02,  1.02,  0.04, -0.03, -0.05,  0.02, -0.06,  0.03],
    [ 0.07,  0.01,  1.04,  0.09,  0.02,  0.05,  0.01,  0.03],
    [ 0.05, -0.02,  0.10,  1.01,  0.08,  0.01,  0.04,  0.02],
    [ 0.11, -0.04,  0.03,  0.06,  1.02,  0.02,  0.07,  0.01],
    [ 0.01,  0.02,  0.05,  0.00,  0.03,  1.03,  0.02,  0.04],
    [ 0.02, -0.05,  0.02,  0.04,  0.08,  0.03,  1.04,  0.00],
    [ 0.00,  0.03,  0.04,  0.02,  0.01,  0.04,  0.00,  1.02]
  ]

  // Interactive demonstration rate: intentionally high enough that structural
  // growth is observable during a short session. Capacity/gain remain bounded.
  morphogenesis Structural {
    probability = 0.18
    max_nodes = 48
    max_connections = 96
    max_operators = 12
    operator_every = 3
    operator_gain = 0.025
    node_noise = 0.06
    min_weight = 0.50
    max_weight = 1.00
    target_matrices = ["F", "V"]
  }

  operator Focus {
    map = clamp(tanh(F @ Psi), 0, 1)
  }

  operator Recall {
    map = clamp(Psi + 0.12 * recall_vector("FieldMemory"), 0, 1)
  }

  operator Volition {
    map = clamp(tanh(V @ Psi), 0, 1)
  }

  // These are actual XC runtime measures, not visual metaphors.
  measure commutator_norm {
    value = norm(F @ V - V @ F)
  }

  measure order_divergence {
    value = norm(Volition(Focus(Psi)) - Focus(Volition(Psi)))
  }

  measure fv_norm {
    value = norm(Volition(Focus(Psi)))
  }

  measure vf_norm {
    value = norm(Focus(Volition(Psi)))
  }

  measure state_norm {
    value = norm(Psi)
  }

  measure memory_norm {
    value = norm(recall_vector("FieldMemory"))
  }

  measure GrowthEvents {
    value = morph_event_count("Structural")
  }

  measure PsiNodes {
    value = morph_node_count("Structural")
  }

  measure TauEdges {
    value = morph_connection_count("Structural")
  }

  measure GrownOperators {
    value = morph_operator_count("Structural")
  }

  actions { FLOW BRANCH CONTRACT RESONATE }

  policy FieldPolicy {
    score FLOW = cohesion + 0.50 * resonance + 0.30 * brightness - 0.60 * distortion
    score BRANCH = branch_pressure + 0.70 * entropy + 0.50 * distortion
    score CONTRACT = cohesion + 0.40 * memory_salience - 0.50 * entropy
    score RESONATE = resonance + 0.70 * oscillation + 0.20 * memory_salience
    select argmax
  }

  cycle {
    Psi <- Focus(Psi)
    Psi <- Recall(Psi)
    Psi <- Volition(Psi)
    action <- FieldPolicy(Psi)
  }

  event MusicPulse {
    observe MusicPulse
    Psi <- clamp(Psi + Obs, 0, 1)
    remember FieldMemory
    cycle 1
    morph Structural
  }

  event HarmonicRise {
    observe HarmonicRise
    Psi <- clamp(Psi + Obs, 0, 1)
    remember FieldMemory
    cycle 1
    morph Structural
  }

  event NovelInput {
    observe NovelInput
    Psi <- clamp(Psi + Obs, 0, 1)
    remember FieldMemory
    cycle 1
    morph Structural
  }

  event Quiet {
    observe Quiet
    Psi <- clamp(Psi + Obs, 0, 1)
    remember FieldMemory
    cycle 1
    morph Structural
  }

  event DialogueInput {
    observe DialogueInput
    Psi <- clamp(Psi + Obs, 0, 1)
    remember FieldMemory
    cycle 1
    morph Structural
  }

  // T(Sigma_tilde, o_t+1): the coupled-environment bridge injects only the
  // encoded observation o here. Memory/retrieval/operators/morphology are
  // deliberately downstream of the sensor boundary.
  event EnvironmentFeedback {
    observe EnvironmentFeedback
    Psi <- clamp(Psi + Obs, 0, 1)
    remember FieldMemory
    cycle 1
    morph Structural
  }
}
