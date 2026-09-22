import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',workers:1,timeout:45000,use:{baseURL:'http://127.0.0.1:3108',headless:true,screenshot:'only-on-failure',trace:'retain-on-failure'},reporter:'list'});
