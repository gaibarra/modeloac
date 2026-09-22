import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const credentials=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../.work/acceso-inicial.json'),'utf8'));
test('Acceso, inventario real, formularios, fuentes, reportes y móvil',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{name:'Bienvenido de nuevo'})).toBeVisible();
 await page.getByLabel('Usuario',{exact:true}).fill(credentials.username);await page.getByLabel('Contraseña',{exact:true}).fill(credentials.password);
 await page.getByRole('button',{name:'Entrar a Modelo AC'}).click();
 await expect(page.getByRole('heading',{name:'Todo bajo control.'})).toBeVisible();
 await page.setViewportSize({width:1440,height:1100});await page.screenshot({path:'../docs/screenshots/dashboard-desktop.png',fullPage:true,animations:'disabled'});
 await page.getByRole('button',{name:'Inventario',exact:true}).click();await expect(page.getByText('318 registros',{exact:true})).toBeVisible();
 await page.getByRole('textbox',{name:'Buscar registros'}).fill('ee452');await expect(page.getByRole('button',{name:'ee452',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'ee452',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByRole('dialog').getByText('Sin registrar',{exact:true}).first()).toBeVisible();await page.getByRole('button',{name:'Cerrar',exact:true}).click();
 await page.getByRole('button',{name:'Nueva alta',exact:true}).click();await expect(page.getByLabel('Código de equipo')).toBeVisible();await expect(page.getByLabel('Modelo técnico').locator('option')).toHaveCount(38);await page.getByRole('button',{name:'Cancelar',exact:true}).click();
 await page.getByRole('button',{name:'Mantenimiento',exact:true}).click();await page.getByRole('button',{name:'Nueva orden de trabajo'}).click();await expect(page.getByLabel(/^Equipo/).locator('option')).toHaveCount(319);await expect(page.getByText('Lista de verificación',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Cancelar',exact:true}).click();
 await page.getByRole('button',{name:'Revisión de datos',exact:true}).click();await page.getByRole('button',{name:/Ver registro/}).first().click();await expect(page.locator('.source-image')).toBeVisible();await expect.poll(()=>page.locator('.source-image').evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBeGreaterThan(0);await page.getByRole('button',{name:'Cerrar',exact:true}).click();
 await page.getByRole('button',{name:'Reportes',exact:true}).click();const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Excel',exact:true}).first().click()]);expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
 for(const name of ['Ubicaciones','Biblioteca técnica','Adquisiciones','Proveedores','Histórico importado','Bitácora']){await page.getByRole('button',{name,exact:true}).click();await expect(page.locator('.page-heading h1')).toBeVisible();await expect(page.locator('.alert-error[role=alert]')).toHaveCount(0);}
 await page.getByRole('button',{name:'Vista general',exact:true}).click();await expect(page.getByRole('heading',{name:'Todo bajo control.'})).toBeVisible();
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'../docs/screenshots/dashboard-mobile.png',fullPage:true,animations:'disabled'});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByRole('button',{name:'Abrir menú'}).click();await page.getByRole('button',{name:'Inventario',exact:true}).click();await expect(page.getByRole('heading',{name:'Inventario de equipos'})).toBeVisible();
 await page.getByRole('button',{name:'Abrir menú'}).click();await page.getByRole('button',{name:'Cerrar sesión'}).click();await expect(page.getByRole('heading',{name:'Bienvenido de nuevo'})).toBeVisible();expect(errors).toEqual([]);
});
