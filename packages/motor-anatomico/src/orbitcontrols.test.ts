import { describe, expect, it } from "vitest";
import { PerspectiveCamera, Quaternion, Vector3 } from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { atualizarEixoOrbitacao } from "./MotorAnatomico";

describe("eixo vertical do OrbitControls", () => {
  it("mantém os quaternions reais e alinha o up superior ao eixo orbital Y", () => {
    const camera = new PerspectiveCamera();
    const orbit = new OrbitControls(camera);
    const controle = orbit as OrbitControls & { _quat: Quaternion; _quatInverse: Quaternion };
    expect(controle._quat).toBeInstanceOf(Quaternion);
    expect(controle._quatInverse).toBeInstanceOf(Quaternion);

    atualizarEixoOrbitacao(camera, orbit, [0, 0, 1]);
    const superiorNoEixoY = new Vector3(0, 0, 1).applyQuaternion(controle._quat);
    expect(superiorNoEixoY.x).toBeCloseTo(0);
    expect(superiorNoEixoY.y).toBeCloseTo(1);
    expect(superiorNoEixoY.z).toBeCloseTo(0);
    expect(controle._quatInverse.clone().multiply(controle._quat).angleTo(new Quaternion())).toBeCloseTo(0);
  });
});
