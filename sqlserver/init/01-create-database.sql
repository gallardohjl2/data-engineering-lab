IF DB_ID('VentasDB') IS NULL
BEGIN
    CREATE DATABASE VentasDB;
END;
GO

USE VentasDB;
GO

CREATE TABLE Productos
(
    producto_id INT PRIMARY KEY,

    nombre VARCHAR(100) NULL,

    categoria VARCHAR(50) NULL,

    precio DECIMAL(10,2) NULL,

    activo BIT NOT NULL DEFAULT 1,

    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE Sucursales
(
    sucursal_id INT PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,

    ciudad VARCHAR(100) NULL,

    estado VARCHAR(100) NULL,

    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO