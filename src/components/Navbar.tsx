'use client'

import React from 'react'
import Link from 'next/link'

const Navbar = () => {
  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-gray-800">
              Your Brand
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-gray-600 hover:text-gray-900">
              Home
            </Link>
            <Link href="/about" className="text-gray-600 hover:text-gray-900">
              About
            </Link>
            <Link href="/schedule" className="text-gray-600 hover:text-gray-900">
              Schedule
            </Link>
            <Link href="/quote" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
              Get Quote
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar 